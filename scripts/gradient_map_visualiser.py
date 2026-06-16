#!/usr/bin/env python3
"""
gradient_map_visualiser.py
==========================
Reads the CSV produced by map_receiver.py and generates two sets of figures:

  Figure 1  Per-sensor spatial maps
            One figure per frequency.  Each subplot shows the magnitude
            recorded by one sensor across all grid positions, as a scatter
            plot coloured by magnitude with an optional interpolated surface.
            Known lamp positions are overlaid as a star marker.

  Figure 2  Aggregate analysis (one figure for all frequencies)
            Row per frequency, three columns:
              col 0  Intensity heatmap  (mean or max across sensors)
              col 1  WLS gradient field
              col 2  Polar sensitivity plot (mean per-sensor magnitude)
            Lamp positions overlaid on heatmap and gradient plots.

USAGE
-----
  Basic:
    python gradient_map_visualiser.py map_data.csv

  With known lamp positions (frequency:x,y  space-separated):
    python gradient_map_visualiser.py map_data.csv \\
        --lamps "150:1.00,2.00  200:3.50,1.20"

  Multiple lamps at the same frequency:
    python gradient_map_visualiser.py map_data.csv \\
        --lamps "150:1.00,2.00  150:4.00,2.00  200:2.50,3.00"

  Skip gradient (faster, useful for first look):
    python gradient_map_visualiser.py map_data.csv --no-gradient

  Save to custom filename prefix:
    python gradient_map_visualiser.py map_data.csv --out-prefix my_run

LAMP FORMAT
-----------
  --lamps "<freq>:<x>,<y>  <freq>:<x>,<y> ..."
  freq must match a frequency present in the data (within 1 Hz tolerance).
  If a lamp's frequency does not match any logged frequency it is shown on
  all frequency plots (useful if you are not sure which lamp is which).

REQUIREMENTS
------------
  pip install numpy pandas matplotlib scipy
"""

import json
import sys
import re
import argparse
from pathlib import Path
from itertools import product as iproduct

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy.interpolate import griddata


# ---------------------------------------------------------------------------
# WLS gradient estimator  (port of blimp.cpp estimate_gradient)
# ---------------------------------------------------------------------------
MIN_MAP_POINTS     = 3
GRADIENT_THRESHOLD = 0.05
MAX_DIST           = 2.0
MIN_DIST           = 0.05
W_EPS              = 0.01


def estimate_gradient_wls(cx, cy, pts_x, pts_y, pts_z):
    dx = cx - pts_x;  dy = cy - pts_y
    d  = np.sqrt(dx**2 + dy**2)
    mask = (d >= MIN_DIST) & (d <= MAX_DIST)
    if mask.sum() < MIN_MAP_POINTS:
        return 0.0, 0.0, 0.0, 0.0, False

    px = pts_x[mask]; py = pts_y[mask]; pz = pts_z[mask]
    w  = 1.0 / (d[mask]**2 + W_EPS);  w /= w.sum()

    sw   = w.sum()
    swx  = (w*px).sum();    swy  = (w*py).sum();    swz  = (w*pz).sum()
    swxx = (w*px*px).sum(); swyy = (w*py*py).sum(); swxy = (w*px*py).sum()
    swxz = (w*px*pz).sum(); swyz = (w*py*pz).sum()

    M   = np.array([[swxx, swxy, swx],
                    [swxy, swyy, swy],
                    [swx,  swy,  sw]])
    rhs = np.array([swxz, swyz, swz])

    if abs(np.linalg.det(M)) < 1e-8:
        return 0.0, 0.0, 0.0, 0.0, False
    try:
        a, b, c = np.linalg.solve(M, rhs)
    except np.linalg.LinAlgError:
        return 0.0, 0.0, 0.0, 0.0, False

    mag    = np.sqrt(a**2 + b**2)
    pred   = a*px + b*py + c
    mean_z = swz / sw
    ss_res = (w*(pz - pred)**2).sum()
    ss_tot = (w*(pz - mean_z)**2).sum()
    r2     = 1.0 - ss_res/ss_tot if ss_tot > 1e-10 else 0.0
    return a, b, mag, r2, r2 >= GRADIENT_THRESHOLD


# ---------------------------------------------------------------------------
# CSV loader  (skips # cfg: comment lines)
# ---------------------------------------------------------------------------
CFG_PREFIX = "# cfg:"

def load_csv(path: Path):
    cfg = {}
    skip_rows = []
    with open(path, "r") as f:
        for i, line in enumerate(f):
            s = line.strip()
            if s.startswith(CFG_PREFIX):
                try:
                    cfg = json.loads(s[len(CFG_PREFIX):])
                except Exception:
                    pass
                skip_rows.append(i)
            elif s.startswith("#"):
                skip_rows.append(i)
    df = pd.read_csv(path, skiprows=skip_rows)
    return df, cfg


# ---------------------------------------------------------------------------
# Lamp position parser
# ---------------------------------------------------------------------------
def parse_lamps(lamp_str: str, frequencies: list[float], step: float) -> list[dict]:
    """
    Parse  "150:1.0,2.0  200:3.5,1.2"  into a list of dicts:
      [{"freq": 150.0, "x": 1.0, "y": 2.0, "label": "150 Hz lamp"},  ...]

    freq=None means "show on all frequencies" (fallback when no match found).
    """
    lamps = []
    for token in lamp_str.split():
        token = token.strip()
        if not token:
            continue
        m = re.fullmatch(r"([0-9.]+):(-?[0-9.]+),(-?[0-9.]+)", token)
        if not m:
            print(f"WARN: Could not parse lamp token '{token}' — expected freq:x,y")
            continue
        req_freq = float(m.group(1))
        lx, ly   = float(m.group(2)) * step, float(m.group(3)) * step

        # Match to a logged frequency within 1 Hz tolerance
        matched = None
        for f in frequencies:
            if abs(f - req_freq) <= 1.0:
                matched = f
                break

        if matched is None:
            print(f"WARN: Lamp freq {req_freq} Hz not found in data "
                  f"(available: {[f'{f:.0f}' for f in frequencies]}) "
                  f"— will show on all frequency plots.")

        lamps.append({
            "freq":  matched,          # None = show everywhere
            "x":     lx,
            "y":     ly,
            "label": f"{req_freq:.0f} Hz lamp",
        })
    return lamps


def overlay_lamps(ax, lamps: list[dict], freq: float):
    """Draw lamp markers on a spatial axes for the given frequency."""
    for lamp in lamps:
        if lamp["freq"] is None or abs(lamp["freq"] - freq) < 0.5:
            ax.plot(lamp["x"], lamp["y"],
                    marker="*", markersize=18, color="lime",
                    markeredgecolor="black", markeredgewidth=0.8,
                    zorder=10, label=lamp["label"])

# ---------------------------------------------------------------------------
# Obstacle helpers
# ---------------------------------------------------------------------------
def parse_obstacles(obs_str: str) -> list[dict]:
    """
    Parse  "x,y,w,h  x,y,w,h ..."  into a list of dicts.
    x,y = bottom-left corner (metres), w = width, h = height.
    Example: --obstacle "0.4,0.2,0.20,0.25"
    """
    obstacles = []
    for token in obs_str.split():
        token = token.strip()
        if not token:
            continue
        parts = token.split(",")
        if len(parts) != 4:
            print(f"WARN: Cannot parse obstacle '{token}' — expected x,y,w,h")
            continue
        try:
            x, y, w, h = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            obstacles.append({"x": x, "y": y, "w": w, "h": h})
        except ValueError:
            print(f"WARN: Cannot parse obstacle '{token}' — values must be numbers")
    return obstacles


def point_in_obstacle(px: float, py: float, obstacles: list[dict],
                       margin: float = 0.0) -> bool:
    """Return True if (px, py) falls inside any obstacle (with optional margin)."""
    for obs in obstacles:
        if (obs["x"] - margin <= px <= obs["x"] + obs["w"] + margin and
                obs["y"] - margin <= py <= obs["y"] + obs["h"] + margin):
            return True
    return False


def overlay_obstacles(ax, obstacles: list[dict]):
    """Draw obstacle rectangles on a spatial axes."""
    for obs in obstacles:
        ax.add_patch(Rectangle(
            (obs["x"], obs["y"]), obs["w"], obs["h"],
            linewidth=1.5, edgecolor="white", facecolor="0.25",
            hatch="////", zorder=8, label="Obstacle"
        ))



# ---------------------------------------------------------------------------
# Shared helper: interpolate and plot a 2-D heatmap on ax
# ---------------------------------------------------------------------------
def plot_heatmap(ax, pts_x, pts_y, pts_z,
                 cmap="inferno", title="", xlabel="x (m)", ylabel="y (m)",
                 scatter_label="", vmin=None, vmax=None, log_scale=False,
                 obstacles=None):
    if vmin is None: vmin = pts_z.min() if len(pts_z) else 0
    if vmax is None: vmax = pts_z.max() if len(pts_z) else 1
    if log_scale:
        # Transform data with log1p so the colour axis is linear in log-space.
        # log1p(x) = log(1+x) is defined at x=0, avoids log(0) for zero magnitudes.
        pts_z = np.log1p(pts_z)
        if vmin is not None: vmin = np.log1p(vmin)
        if vmax is not None: vmax = np.log1p(vmax)
    norm = Normalize(vmin=vmin if vmin is not None else pts_z.min(),
                     vmax=vmax if vmax is not None else pts_z.max())

    if len(pts_x) >= 3:
        xi = np.linspace(pts_x.min(), pts_x.max(), 200)
        yi = np.linspace(pts_y.min(), pts_y.max(), 200)
        Xi, Yi = np.meshgrid(xi, yi)
        try:
            Zi = griddata((pts_x, pts_y), pts_z, (Xi, Yi), method="cubic")
        except Exception:
            Zi = griddata((pts_x, pts_y), pts_z, (Xi, Yi), method="nearest")

        # Blank interpolated cells that fall inside any obstacle
        if obstacles:
            for obs in obstacles:
                mask = ((Xi >= obs["x"]) & (Xi <= obs["x"] + obs["w"]) &
                        (Yi >= obs["y"]) & (Yi <= obs["y"] + obs["h"]))
                Zi[mask] = np.nan   # nan renders as transparent in pcolormesh

        im = ax.pcolormesh(Xi, Yi, Zi, cmap=cmap, norm=norm, shading="auto", alpha=0.8)
    else:
        # Not enough points for interpolation — just scatter
        im = ScalarMappable(norm=norm, cmap=cmap)
        im.set_array([])

    ax.scatter(pts_x, pts_y, c=pts_z, cmap=cmap, norm=norm,
               edgecolors="white", linewidths=0.4, s=55, zorder=5,
               label=scatter_label or "Measured")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel(ylabel, fontsize=8)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7)

    # Draw obstacle rectangles on top of the heatmap
    if obstacles:
        overlay_obstacles(ax, obstacles)

    return im


# ---------------------------------------------------------------------------
# Figure 1b: per-sensor SNR maps  (one figure per frequency, mirrors Fig 1)
# ---------------------------------------------------------------------------
def plot_per_sensor_snr_maps(df: pd.DataFrame, freq: float,
                              lamps: list, out_prefix: str):
    """Same layout as plot_per_sensor_maps but coloured by SNR instead of magnitude."""
    if "snr" not in df.columns:
        return
    sub = df[df["frequency_hz"] == freq]
    sensors = sorted(sub["sensor_name"].unique(),
                     key=lambda s: sub[sub["sensor_name"]==s]["sensor_angle_deg"].iloc[0])
    n = len(sensors)
    if n == 0:
        return

    ncols = min(4, n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 4.5, nrows * 4.0),
                             squeeze=False)
    fig.suptitle(f"Per-Sensor SNR Maps  —  {freq:.0f} Hz\n"
                 f"({n} sensors, {sub[['x','y']].drop_duplicates().shape[0]} positions)",
                 fontsize=13, fontweight="bold")

    global_vmin = sub["snr"].min()
    global_vmax = sub["snr"].max()

    for idx, sensor_name in enumerate(sensors):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        s_data = sub[sub["sensor_name"] == sensor_name]
        angle  = s_data["sensor_angle_deg"].iloc[0]

        im = plot_heatmap(ax, s_data["x"].values, s_data["y"].values,
                          s_data["snr"].values,
                          cmap="viridis",
                          title=f"{sensor_name}  ({angle:.1f}°)",
                          vmin=global_vmin, vmax=global_vmax)
        overlay_lamps(ax, lamps, freq)
        if idx == 0 and lamps:
            ax.legend(fontsize=7, loc="upper right")

    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.subplots_adjust(right=0.88, hspace=0.45, wspace=0.35)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    sm = ScalarMappable(norm=Normalize(vmin=global_vmin, vmax=global_vmax),
                        cmap="viridis")
    sm.set_array([])
    fig.colorbar(sm, cax=cbar_ax, label="SNR")

    out_path = Path(f"{out_prefix}_{freq:.0f}hz_per_sensor_snr.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  Per-sensor SNR figure saved: '{out_path}'")
    return fig


# ---------------------------------------------------------------------------
# Figure 3: DC level saturation check  (one figure per frequency)
# ---------------------------------------------------------------------------
def plot_dc_saturation(df: pd.DataFrame, freq: float,
                       lamps: list, out_prefix: str):
    """
    Per-sensor map of the mean DC light level (raw ADC counts, 0-4095).
    High values indicate the photodiode may be saturating, which would
    reduce the AC signal amplitude and make magnitude / SNR unreliable.
    A horizontal dashed line at 4095 on the shared colour scale shows the
    saturation ceiling.
    """
    if "dc_level" not in df.columns:
        print("  NOTE: No dc_level column — skipping saturation figure.")
        return None

    sub = df[df["frequency_hz"] == freq]
    sensors = sorted(sub["sensor_name"].unique(),
                     key=lambda s: sub[sub["sensor_name"]==s]["sensor_angle_deg"].iloc[0])
    n = len(sensors)
    if n == 0:
        return None

    ncols = min(4, n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 4.5, nrows * 4.0),
                             squeeze=False)
    fig.suptitle(f"DC Light Level (Saturation Check)  —  {freq:.0f} Hz\n"
                 f"Colour scale: 0 – 4095 ADC counts  (4095 = saturated)",
                 fontsize=13, fontweight="bold")

    # Always use the full 12-bit range so severity is immediately visible
    VMAX = 4095.0

    for idx, sensor_name in enumerate(sensors):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        s_data = sub[sub["sensor_name"] == sensor_name]
        angle  = s_data["sensor_angle_deg"].iloc[0]
        dc_max = s_data["dc_level"].max()

        # Warn in the subplot title if any reading is >90 % of full scale
        saturated = dc_max > 0.9 * VMAX
        title = f"{sensor_name}  ({angle:.1f}°)"
        if saturated:
            title += "  ⚠ NEAR SAT"

        im = plot_heatmap(ax, s_data["x"].values, s_data["y"].values,
                          s_data["dc_level"].values,
                          cmap="RdYlGn_r",   # green=low, red=high/saturated
                          title=title,
                          vmin=0.0, vmax=VMAX)
        overlay_lamps(ax, lamps, freq)
        if idx == 0 and lamps:
            ax.legend(fontsize=7, loc="upper right")

    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.subplots_adjust(right=0.88, hspace=0.45, wspace=0.35)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    sm = ScalarMappable(norm=Normalize(vmin=0.0, vmax=VMAX), cmap="RdYlGn_r")
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax, label="Mean DC level (ADC counts)")
    cb.ax.axhline(y=VMAX * 0.9, color="red", linewidth=1.5, linestyle="--")

    out_path = Path(f"{out_prefix}_{freq:.0f}hz_dc_saturation.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  DC saturation figure saved: '{out_path}'")
    return fig



# ---------------------------------------------------------------------------
# Figure 1: per-sensor spatial maps  (one figure per frequency)
# ---------------------------------------------------------------------------
def plot_per_sensor_maps(df: pd.DataFrame, freq: float,
                         lamps: list[dict], out_prefix: str,
                         log_scale: bool = False, obstacles=None):
    sub = df[df["frequency_hz"] == freq]
    sensors = sorted(sub["sensor_name"].unique(),
                     key=lambda s: sub[sub["sensor_name"]==s]["sensor_angle_deg"].iloc[0])
    n = len(sensors)
    if n == 0:
        print(f"  No sensors found for {freq:.0f} Hz — skipping per-sensor figure.")
        return

    ncols = min(4, n)
    nrows = int(np.ceil(n / ncols))
    scale_label = " (log scale)" if log_scale else ""

    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 4.5, nrows * 4.0),
                             squeeze=False)
    fig.suptitle(f"Per-Sensor Magnitude Maps{scale_label}  —  {freq:.0f} Hz\n"
                 f"({n} sensors, {sub[['x','y']].drop_duplicates().shape[0]} positions)",
                 fontsize=13, fontweight="bold")

    # Shared colour scale across all sensors for fair comparison
    global_vmin = sub["magnitude"].min()
    global_vmax = sub["magnitude"].max()

    for idx, sensor_name in enumerate(sensors):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]

        s_data = sub[sub["sensor_name"] == sensor_name]
        pts_x  = s_data["x"].values
        pts_y  = s_data["y"].values
        pts_z  = s_data["magnitude"].values
        angle  = s_data["sensor_angle_deg"].iloc[0]

        im = plot_heatmap(ax, pts_x, pts_y, pts_z,
                          cmap="inferno",
                          title=f"{sensor_name}  ({angle:.1f}°)",
                          vmin=global_vmin, vmax=global_vmax,
                          log_scale=log_scale,
                          obstacles=obstacles)

        overlay_lamps(ax, lamps, freq)
        if idx == 0 and lamps:
            ax.legend(fontsize=7, loc="upper right")

    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    fig.subplots_adjust(right=0.88, hspace=0.45, wspace=0.35)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    cb_vmin = np.log1p(global_vmin) if log_scale else global_vmin
    cb_vmax = np.log1p(global_vmax) if log_scale else global_vmax
    cb_label = "log(1 + Magnitude)" if log_scale else "Magnitude"
    sm = ScalarMappable(norm=Normalize(vmin=cb_vmin, vmax=cb_vmax), cmap="inferno")
    sm.set_array([])
    fig.colorbar(sm, cax=cbar_ax, label=cb_label)

    suffix = "_log" if log_scale else ""
    out_path = Path(f"{out_prefix}_{freq:.0f}hz_per_sensor{suffix}.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  Per-sensor figure saved: '{out_path}'")
    return fig


# ---------------------------------------------------------------------------
# Figure 2: gradient comparison  — one figure per (frequency × variant)
#
# variant is a dict with keys:
#   pts_z    : numpy array of scalar values at each position (already aggregated)
#   label    : short human-readable name,  e.g. "Magnitude mean"
#   suffix   : filename suffix,            e.g. "mag_mean"
#   cbar     : colourbar label,            e.g. "Magnitude (mean)"
# ---------------------------------------------------------------------------
def _compute_gradient_field(pts_x, pts_y, pts_z, resolution,
                             obstacles=None):
    """
    Run WLS gradient over a query grid.

    Obstacle handling:
    - Query points inside an obstacle are skipped entirely (Ok stays False,
      so no arrows are drawn there).
    - Data points inside an obstacle are excluded from the neighbour search,
      so the gradient at nearby positions is not pulled by phantom readings
      from inside the box.

    Returns (qx, qy, Gx, Gy, Mag, R2, Ok).
    """
    qx = np.arange(pts_x.min(), pts_x.max() + resolution, resolution)
    qy = np.arange(pts_y.min(), pts_y.max() + resolution, resolution)
    Gx  = np.zeros((len(qy), len(qx)))
    Gy  = np.zeros((len(qy), len(qx)))
    Mag = np.zeros((len(qy), len(qx)))
    R2  = np.zeros((len(qy), len(qx)))
    Ok  = np.zeros((len(qy), len(qx)), dtype=bool)

    # Pre-filter data points: exclude any that lie inside an obstacle
    if obstacles:
        keep = np.array([not point_in_obstacle(px, py, obstacles)
                         for px, py in zip(pts_x, pts_y)])
        filt_x = pts_x[keep]
        filt_y = pts_y[keep]
        filt_z = pts_z[keep]
    else:
        filt_x, filt_y, filt_z = pts_x, pts_y, pts_z

    for ci, cx in enumerate(qx):
        for ri, cy in enumerate(qy):
            # Skip query points inside obstacles — leave as Ok=False
            if obstacles and point_in_obstacle(cx, cy, obstacles):
                continue
            gx, gy, mag, r2, valid = estimate_gradient_wls(
                cx, cy, filt_x, filt_y, filt_z)
            Gx[ri,ci]=gx; Gy[ri,ci]=gy
            Mag[ri,ci]=mag; R2[ri,ci]=r2; Ok[ri,ci]=valid
    return qx, qy, Gx, Gy, Mag, R2, Ok


def plot_gradient_variant(df: pd.DataFrame,
                          freq: float,
                          variant: dict,
                          lamps: list,
                          resolution: float,
                          out_prefix: str,
                          obstacles=None):
    """
    One figure for one (frequency, variant) combination.
    Layout: [intensity heatmap] [WLS gradient field]
    Polar sensitivity is produced separately by plot_polar_sensitivity.
    Obstacles are blanked in the heatmap and excluded from the WLS computation.
    """
    pts_x = variant["pts_x"]
    pts_y = variant["pts_y"]
    pts_z = variant["pts_z"]

    fig, (ax_heat, ax_grad) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"{freq:.0f} Hz  —  {variant['label']}",
                 fontsize=13, fontweight="bold")

    # ---- Intensity heatmap ----
    plot_heatmap(ax_heat, pts_x, pts_y, pts_z,
                 title=f"Intensity  ({variant['label']})",
                 scatter_label="Measured",
                 obstacles=obstacles)
    sm = ScalarMappable(norm=Normalize(pts_z.min(), pts_z.max()), cmap="inferno")
    sm.set_array([])
    plt.colorbar(sm, ax=ax_heat, label=variant["cbar"])
    overlay_lamps(ax_heat, lamps, freq)
    if lamps:
        ax_heat.legend(fontsize=8)

    # ---- WLS Gradient ----
    if len(pts_x) >= MIN_MAP_POINTS:
        qx, qy, Gx, Gy, GradMag, R2, Ok = _compute_gradient_field(
            pts_x, pts_y, pts_z, resolution, obstacles=obstacles)

        # Blank R² cells inside obstacles so they render as transparent
        if obstacles:
            QXb, QYb = np.meshgrid(qx, qy)
            for obs in obstacles:
                obs_mask = ((QXb >= obs["x"]) & (QXb <= obs["x"] + obs["w"]) &
                            (QYb >= obs["y"]) & (QYb <= obs["y"] + obs["h"]))
                R2[obs_mask] = np.nan

        im2 = ax_grad.pcolormesh(qx, qy, R2, cmap="Blues",
                                  vmin=0, vmax=1, shading="auto", alpha=0.6)
        plt.colorbar(im2, ax=ax_grad, label="WLS R²")

        QX, QY = np.meshgrid(qx, qy)
        mask   = Ok & (GradMag > 0)
        scale  = GradMag[mask].max() if mask.any() else 1.0
        ax_grad.quiver(QX[mask], QY[mask],
                       Gx[mask]/(scale+1e-9), Gy[mask]/(scale+1e-9),
                       color="crimson", scale=10, width=0.004, label="gradient")
        ax_grad.scatter(pts_x, pts_y, c="black", s=25, zorder=5, label="Measured")
        overlay_lamps(ax_grad, lamps, freq)
        if obstacles:
            overlay_obstacles(ax_grad, obstacles)

        valid_pct = 100.0 * Ok.sum() / Ok.size if Ok.size else 0
        print(f"    [{variant['suffix']}] gradient: {Ok.sum()}/{Ok.size} cells valid "
              f"({valid_pct:.1f}%)")
    else:
        ax_grad.text(0.5, 0.5, "Too few points", ha="center", va="center",
                     transform=ax_grad.transAxes, fontsize=10, color="grey")

    ax_grad.set_title(f"WLS Gradient  (R\u00b2\u2265{GRADIENT_THRESHOLD})")
    ax_grad.set_xlabel("x (m)"); ax_grad.set_ylabel("y (m)")
    ax_grad.legend(fontsize=8); ax_grad.set_aspect("equal")

    plt.tight_layout()
    out_path = Path(f"{out_prefix}_{freq:.0f}hz_gradient_{variant['suffix']}.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  Saved: '{out_path}'")
    plt.close(fig)

def build_gradient_variants(df: pd.DataFrame, freq: float) -> list[dict]:
    """
    Build the list of aggregation variants to plot for one frequency.
    Returns a list of dicts ready for plot_gradient_variant.
    """
    sub = df[df["frequency_hz"] == freq]
    has_snr = "snr" in sub.columns
    variants = []

    pos_cols = ["x", "y"]

    for agg_fn, agg_name, agg_suffix in [("mean", "mean", "mean"), ("max", "max", "max")]:
        # ---- Magnitude (linear) ----
        grp = sub.groupby(pos_cols)["magnitude"].agg(agg_fn).reset_index()
        variants.append({
            "pts_x":  grp["x"].values,
            "pts_y":  grp["y"].values,
            "pts_z":  grp["magnitude"].values,
            "label":  f"Magnitude {agg_name}",
            "suffix": f"mag_{agg_suffix}",
            "cbar":   f"Magnitude ({agg_name})",
        })

        # ---- Magnitude (log-transformed) ----
        grp_log = grp.copy()
        grp_log["magnitude"] = np.log1p(grp_log["magnitude"])
        variants.append({
            "pts_x":  grp_log["x"].values,
            "pts_y":  grp_log["y"].values,
            "pts_z":  grp_log["magnitude"].values,
            "label":  f"log(1 + Magnitude {agg_name})",
            "suffix": f"mag_{agg_suffix}_log",
            "cbar":   f"log(1 + Magnitude) ({agg_name})",
        })

        # ---- SNR ----
        if has_snr:
            grp_snr = sub.groupby(pos_cols)["snr"].agg(agg_fn).reset_index()
            variants.append({
                "pts_x":  grp_snr["x"].values,
                "pts_y":  grp_snr["y"].values,
                "pts_z":  grp_snr["snr"].values,
                "label":  f"SNR {agg_name}",
                "suffix": f"snr_{agg_suffix}",
                "cbar":   f"SNR ({agg_name})",
            })

    return variants


# ---------------------------------------------------------------------------
# Figure 4: sensor-aggregated statistics overview
#
# For each frequency: one figure with 2 rows x 3 cols (or 1 row x 3 cols if
# no SNR column).
#
#   Row 0 — Magnitude : min | mean | max  across all sensors at each position
#   Row 1 — SNR       : min | mean | max  across all sensors at each position
#
# All three magnitude subplots share the same colour scale so spatial
# gradients and hot-spots are directly comparable.  Same for SNR.
# Lamp positions are overlaid on every subplot.
# ---------------------------------------------------------------------------
def plot_stats_overview(df: pd.DataFrame, freq: float,
                        lamps: list, out_prefix: str):
    sub = df[df["frequency_hz"] == freq]
    if sub.empty:
        return None

    has_snr = "snr" in sub.columns
    stats_rows = []

    # ---- Magnitude stats per position ----
    mag_stats = (sub.groupby(["x", "y"])["magnitude"]
                 .agg(["min", "mean", "max"])
                 .reset_index())
    stats_rows.append({
        "label":  "Magnitude",
        "unit":   "FFT magnitude",
        "cmap":   "inferno",
        "stats":  mag_stats,
        "col":    "magnitude",
    })

    # ---- SNR stats per position ----
    if has_snr:
        snr_stats = (sub.groupby(["x", "y"])["snr"]
                     .agg(["min", "mean", "max"])
                     .reset_index())
        stats_rows.append({
            "label":  "SNR",
            "unit":   "SNR",
            "cmap":   "viridis",
            "stats":  snr_stats,
            "col":    "snr",
        })

    nrows = len(stats_rows)
    ncols = 3
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 5.5, nrows * 4.8),
                             squeeze=False)
    fig.suptitle(
        f"Sensor-Aggregated Statistics Overview  —  {freq:.0f} Hz\n"
        f"Min / Mean / Max across all {sub['sensor_name'].nunique()} sensors"
        f"  ·  {sub[['x','y']].drop_duplicates().shape[0]} positions",
        fontsize=14, fontweight="bold"
    )

    col_titles = ["Minimum", "Mean", "Maximum"]

    for row_idx, row_cfg in enumerate(stats_rows):
        stats   = row_cfg["stats"]
        cmap    = row_cfg["cmap"]
        label   = row_cfg["label"]
        unit    = row_cfg["unit"]

        pts_x = stats["x"].values
        pts_y = stats["y"].values

        # Shared colour scale across the three columns for this metric
        vmin = stats[["min", "mean", "max"]].min().min()
        vmax = stats[["min", "mean", "max"]].max().max()
        # Give a tiny margin so uniform grids don't collapse to a single colour
        if np.isclose(vmin, vmax):
            vmax = vmin + 1.0

        for col_idx, stat_key in enumerate(["min", "mean", "max"]):
            ax    = axes[row_idx][col_idx]
            pts_z = stats[stat_key].values

            im = plot_heatmap(ax, pts_x, pts_y, pts_z,
                              cmap=cmap,
                              title=f"{col_titles[col_idx]} {label}",
                              vmin=vmin, vmax=vmax)
            overlay_lamps(ax, lamps, freq)

            # Only show lamp legend on the first subplot of each row
            if col_idx == 0 and lamps:
                ax.legend(fontsize=7, loc="upper right")

            # Annotate each measured point with its value
            for _, row in stats.iterrows():
                ax.annotate(f"{row[stat_key]:.0f}",
                            xy=(row["x"], row["y"]),
                            fontsize=5, ha="center", va="bottom",
                            color="white", fontweight="bold",
                            xytext=(0, 4), textcoords="offset points")

        # Shared colourbar for this row
        fig.subplots_adjust(right=0.88, hspace=0.40, wspace=0.30)
        cbar_ax = fig.add_axes([
            0.90,
            0.10 + (nrows - 1 - row_idx) * (0.80 / nrows),
            0.018,
            0.72 / nrows
        ])
        sm = ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap)
        sm.set_array([])
        fig.colorbar(sm, cax=cbar_ax, label=unit)

    out_path = Path(f"{out_prefix}_{freq:.0f}hz_stats_overview.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"  Stats overview saved: '{out_path}'")
    return fig


# ---------------------------------------------------------------------------
# Thesis panels: one clean single-axes figure per (frequency, metric).
#
# Each panel is the max-across-sensors field for one beacon frequency, with
# the WLS gradient arrows overlaid and BOTH lamp positions marked, so a single
# panel shows that the field rises toward its own light.  Panels are saved
# separately and composed into a grid with LaTeX subfigure, which keeps the
# page layout adjustable without re-running the script.
# ---------------------------------------------------------------------------
def overlay_all_lamps(ax, lamps, freq):
    """Mark every lamp; highlight the one matching this panel's frequency."""
    for lamp in lamps:
        own = (lamp["freq"] is None) or (abs(lamp["freq"] - freq) < 0.5)
        ax.plot(lamp["x"], lamp["y"], marker="*", linestyle="none",
                markersize=20 if own else 13,
                color="lime" if own else "white",
                markeredgecolor="black", markeredgewidth=1.0, zorder=11,
                label=lamp["label"] if own else lamp["label"] + " (other)")


def plot_metric_panel(df, freq, metric, lamps, resolution, out_prefix,
                      show_legend=True, draw_gradient=False):
    """One self-contained panel: max-across-sensors <metric> field.

    Gradient arrows are off by default: on the raw bench magnitude the
    per-cell direction estimates are unreliable, so the clean heatmap is
    left to carry the spatial-separation message on its own.
    """
    col, cmap, cbar = {
        "snr":       ("snr",       "viridis", "SNR (max across sensors)"),
        "magnitude": ("magnitude", "inferno", "FFT magnitude (max across sensors)"),
    }[metric]
    if col not in df.columns:
        return
    sub = df[df["frequency_hz"] == freq]
    grp = sub.groupby(["x", "y"])[col].max().reset_index()
    pts_x, pts_y, pts_z = grp["x"].values, grp["y"].values, grp[col].values

    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    plot_heatmap(ax, pts_x, pts_y, pts_z, cmap=cmap, title="",
                 scatter_label="Measured")
    sm = ScalarMappable(norm=Normalize(pts_z.min(), pts_z.max()), cmap=cmap)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label=cbar, fraction=0.046, pad=0.04)

    # WLS gradient arrows overlaid directly on the field (off by default)
    if draw_gradient and len(pts_x) >= MIN_MAP_POINTS:
        qx, qy, Gx, Gy, GMag, R2, Ok = _compute_gradient_field(
            pts_x, pts_y, pts_z, resolution)
        QX, QY = np.meshgrid(qx, qy)
        mask  = Ok & (GMag > 0)
        scale = GMag[mask].max() if mask.any() else 1.0
        ax.quiver(QX[mask], QY[mask],
                  Gx[mask] / (scale + 1e-9), Gy[mask] / (scale + 1e-9),
                  color="#00e5ff", scale=12, width=0.005, zorder=9,
                  label="WLS gradient")

    overlay_all_lamps(ax, lamps, freq)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    if show_legend:
        ax.legend(fontsize=7, loc="upper right", framealpha=0.85)

    out_path = Path(f"{out_prefix}_panel_{freq:.0f}hz_{metric}.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Panel saved: '{out_path}'")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Visualise Teensy gradient map — per-sensor maps + aggregate analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gradient_map_visualiser.py map_data.csv
  python gradient_map_visualiser.py map_data.csv --lamps "150:1.0,2.0  200:3.5,1.2"
  python gradient_map_visualiser.py map_data.csv --no-gradient
  python gradient_map_visualiser.py map_data.csv --aggregate max --resolution 0.05
        """)

    parser.add_argument("csv_file",
                        help="CSV produced by map_receiver.py")
    parser.add_argument("--lamps", default=None,
                        help='Known lamp positions: "freq:x,y  freq:x,y ..."  '
                             'e.g. "150:1.0,2.0  200:3.5,1.2"')
    parser.add_argument("--resolution", type=float, default=0.1,
                        help="Gradient query resolution in metres (default 0.1)")
    parser.add_argument("--no-gradient", action="store_true",
                        help="Skip WLS gradient computation")
    parser.add_argument("--no-per-sensor", action="store_true",
                        help="Skip per-sensor figure (only show aggregate)")
    parser.add_argument("--step", type=float, default=None,
                        help="Grid step in metres — read from CSV config if omitted")
    parser.add_argument("--out-prefix", default=None,
                        help="Output filename prefix (default: CSV basename)")
    parser.add_argument("--obstacle", default=None, metavar="RECT",
                        help='Obstacle rectangle(s) as "x,y,w,h" (metres, bottom-left corner). '
                             'Space-separate multiple: "0.4,0.2,0.20,0.25 1.0,0.6,0.15,0.20"')
    parser.add_argument("--no-saturation", action="store_true",
                        help="Skip DC saturation check figures")
    parser.add_argument("--no-stats", action="store_true",
                        help="Skip sensor-aggregated statistics overview")
    parser.add_argument("--log-scale", action="store_true",
                    help="Also produce log-scale magnitude figures "
                            "(saved with _log suffix alongside the linear versions)")
    parser.add_argument("--panels", action="store_true",
                    help="Emit one clean single-axes panel per (frequency, metric) "
                         "with gradient arrows and both lamps, for LaTeX composition")
    parser.add_argument("--only-panels", action="store_true",
                    help="Produce only the thesis panels and skip every other figure")
    parser.add_argument("--panel-arrows", action="store_true",
                    help="Overlay WLS gradient arrows on the thesis panels "
                         "(off by default; unreliable on raw bench magnitude)")
    args = parser.parse_args()
    if args.only_panels:
        args.panels = True
        args.no_per_sensor = args.no_gradient = True
        args.no_stats = args.no_saturation = True

    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"ERROR: file not found: {csv_path}")
        sys.exit(1)

    out_prefix = args.out_prefix or csv_path.stem

    # --- Load ---
    df, cfg = load_csv(csv_path)
    print(f"Loaded {len(df)} rows from '{csv_path}'")
    if cfg:
        print(f"Session config: {cfg}")

    # --- Validate ---
    required = {"x", "y", "frequency_hz", "sensor_name",
                "sensor_angle_deg", "magnitude"}
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: CSV missing columns: {missing}")
        print(f"       Columns found: {list(df.columns)}")
        sys.exit(1)
    has_snr = "snr" in df.columns
    if not has_snr:
        print("NOTE: No SNR column found — SNR plots will be skipped.")

    # --- Grid step ---
    step = args.step or cfg.get("step") or None
    if step is None:
        ux = np.sort(df["x"].unique())
        step = float(np.min(np.diff(ux))) if len(ux) > 1 else 1.0
        print(f"Grid step estimated from data: {step:.4f} m")
    df["grid_x"] = (df["x"] / step).round().astype(int)
    df["grid_y"] = (df["y"] / step).round().astype(int)

    # --- Summary ---
    frequencies = sorted(df["frequency_hz"].unique())
    sensors     = sorted(df["sensor_name"].unique())
    n_pos       = df[["x","y"]].drop_duplicates().shape[0]
    print(f"\nFrequencies : {[f'{f:.0f} Hz' for f in frequencies]}")
    print(f"Sensors     : {len(sensors)}")
    print(f"Positions   : {n_pos}")
    print(f"Grid step   : {step} m\n")

    # --- Parse lamp positions ---
    lamps     = parse_lamps(args.lamps, frequencies, step) if args.lamps else []
    obstacles = parse_obstacles(args.obstacle) if args.obstacle else []
    if obstacles:
        print("Obstacles:")
        for obs in obstacles:
            print(f"  x={obs['x']:.3f}, y={obs['y']:.3f}, "
                  f"w={obs['w']:.3f}, h={obs['h']:.3f}")
        print()
    if lamps:
        print("Lamp positions:")
        for lp in lamps:
            freq_str = f"{lp['freq']:.0f} Hz" if lp["freq"] is not None else "all freqs"
            print(f"  {lp['label']}  at ({lp['x']:.3f}, {lp['y']:.3f})  [{freq_str}]")
        print()


    # -------------------------------------------------------------------
    # Figure 1: per-sensor magnitude maps (one figure per frequency)
    # -------------------------------------------------------------------
    if not args.no_per_sensor:
        print("=== Per-sensor magnitude figures ===")
        for freq in frequencies:
            print(f"  Plotting {freq:.0f} Hz per-sensor magnitude map...")
            plot_per_sensor_maps(df, freq, lamps, out_prefix,
                                 obstacles=obstacles)
        if args.log_scale:
            print("=== Per-sensor magnitude figures (log scale) ===")
            for freq in frequencies:
                print(f"  Plotting {freq:.0f} Hz per-sensor magnitude map (log)...")
                plot_per_sensor_maps(df, freq, lamps, out_prefix,
                                     log_scale=True, obstacles=obstacles)

    # -------------------------------------------------------------------
    # Figure 1b: per-sensor SNR maps (one figure per frequency)
    # -------------------------------------------------------------------
    if not args.no_per_sensor and has_snr:
        print("\n=== Per-sensor SNR figures ===")
        for freq in frequencies:
            print(f"  Plotting {freq:.0f} Hz per-sensor SNR map...")
            plot_per_sensor_snr_maps(df, freq, lamps, out_prefix)

    # -------------------------------------------------------------------
    # Thesis panels: one clean single-axes panel per (frequency, metric)
    # -------------------------------------------------------------------
    if args.panels:
        print("\n=== Thesis panels (single-axes, for LaTeX composition) ===")
        metrics = (["snr"] if has_snr else []) + ["magnitude"]
        first = True
        for freq in frequencies:
            for metric in metrics:
                # Legend on the first panel only; caption explains the rest.
                plot_metric_panel(df, freq, metric, lamps,
                                  args.resolution, out_prefix,
                                  show_legend=first,
                                  draw_gradient=args.panel_arrows)
                first = False

    # -------------------------------------------------------------------
    # Figure 2: gradient comparison across all variants
    # (magnitude mean/max, log-magnitude mean/max, SNR mean/max)
    # -------------------------------------------------------------------
    if not args.no_gradient:
        print("\n=== Gradient comparison figures ===")
        for freq in frequencies:
            variants = build_gradient_variants(df, freq)
            print(f"  {freq:.0f} Hz — {len(variants)} variants")
            for v in variants:
                print(f"    [{v['suffix']}] ...")
                plot_gradient_variant(df, freq, v, lamps,
                                      args.resolution, out_prefix,
                                      obstacles=obstacles)

    # -------------------------------------------------------------------
    # Figure 2b: sensor-aggregated statistics overview (one per frequency)
    # -------------------------------------------------------------------
    if not args.no_stats:
        print("\n=== Stats overview figures ===")
        for freq in frequencies:
            print(f"  Plotting {freq:.0f} Hz stats overview...")
            plot_stats_overview(df, freq, lamps, out_prefix)

    # -------------------------------------------------------------------
    # Figure 3: DC saturation check (one per frequency)
    # -------------------------------------------------------------------
    if not args.no_saturation:
        has_dc = "dc_level" in df.columns
        if has_dc:
            print("\n=== DC saturation figures ===")
            for freq in frequencies:
                print(f"  Plotting {freq:.0f} Hz DC saturation map...")
                plot_dc_saturation(df, freq, lamps, out_prefix)
        else:
            print("\nNo dc_level column in CSV — skipping saturation figures.")
            print("  (Re-run a mapping session with the updated firmware to capture DC level.)")

    plt.show()


if __name__ == "__main__":
    main()