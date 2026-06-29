"""
plot_session.py
Flexible plotter for CrazyFlie session CSVs (navigation and survey flights).

── Output ────────────────────────────────────────────────────────────────────
Navigation flight  →  time-series panels  +  per-waypoint SNR heatmap(s)
Survey / lawnmower →  time-series panels  +  side-by-side raw / smoothed map

Missing columns are silently skipped; per-channel SNR columns (nav.snr0…snr7)
are stored as int16 ×100 and divided back to float automatically.

── Basic usage ───────────────────────────────────────────────────────────────
  python plot_session.py                        # interactive picker from runs/
  python plot_session.py path/to/session.csv
  python plot_session.py session.csv --save     # save all figures as one PDF

── Heatmap options ───────────────────────────────────────────────────────────
  --bin M               Bin size in metres (default 0.05 = 5 cm)
  --no-gradient         Hide gradient-angle arrows on navigation heatmaps
  --gradient-stride N   Arrow density: one arrow every N bins (default 1)

── Per-waypoint split ────────────────────────────────────────────────────────
  --per-waypoint        One time-series figure + one heatmap per waypoint;
                        time resets to 0 at the start of each waypoint.

── Time-series panel selection ──────────────────────────────────────────────
  By default all panels with available data are stacked into one figure.
  --panels KEY1,KEY2    Only show the listed panels (comma-separated).
                        Choices: state, snr, snr_ch, bearing, grad_angle,
                                 grad_r2, mapsize, weights
                        e.g. --panels snr            (overall SNR only)
                             --panels snr,snr_ch      (overall + per-channel)

── Survey / lawnmower mode ───────────────────────────────────────────────────
  Activated automatically when the filename contains:
    data_gather, survey, scan, lawnmower, lawn, grid
  Override with --survey / --no-survey.

  --survey              Force survey mode
  --no-survey           Force navigation mode
  --smooth-sigma S      Gaussian smoothing radius in bins (default 3.0;
                        set to 0 to disable)
  --light X Y           Mark a light source at (X, Y) m  [repeatable]

── Obstacles ─────────────────────────────────────────────────────────────────
  Auto-parsed from filenames produced by data_gather_rect.py:
    …_obs{cx}-{cy}m_{w}x{d}cm…
  Override / add manually:
  --obstacle CX CY W D  Rectangular obstacle: centre (CX, CY) m, size W×D m
                        [repeatable]
"""

import argparse
import re
import os
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as fst

# Default on-page width fraction (overridden by --page-frac). Figures are drawn
# at scale 1 (figsize width = frac * textwidth) so saved PNGs are page-accurate.
PAGE_FRAC = 1.0

# ── Heatmap settings ─────────────────────────────────────────────────────────
SNR_MAP_BIN_M        = 0.05   # default bin size (5 cm — matches firmware map grid)
SNR_MAP_COLS         = {'stateEstimate.x', 'stateEstimate.y', 'nav.snr'}

# ── Survey / lawnmower mode ───────────────────────────────────────────────────
# Files whose stem contains any of these words are treated as survey flights
# automatically (overridden by explicit --survey / --no-survey flags).
SURVEY_KEYWORDS      = ('survey', 'scan', 'lawnmower', 'lawn', 'grid', 'data_gather')

# ── Gradient acceptance thresholds ───────────────────────────────────────────
# Mirror the firmware defaults (nav.minMapPts and wlsCtrl.mapR2 params).
# Adjust here if you change them in navigate_example.py.
R2_ACCEPT_THRESHOLD  = 0.5   # nav.gradR2 must be >= this
MIN_MAP_CELLS        = 3     # wlsCtrl.mapSize must be >= this

# ── Nav state labels ─────────────────────────────────────────────────────────
NAV_STATES = {
    0: 'IDLE',
    1: 'SEARCHING',
    2: 'ALIGNING',
    3: 'APPROACHING',
    4: 'DWELLING',
    5: 'RECOVERING',
    6: 'COMPLETE',
}

# ── Panel definitions ─────────────────────────────────────────────────────────
# Each entry:
#   title   – subplot title
#   ylabel  – y-axis label
#   step    – True for step plots (integer/state signals)
#   series  – list of (column, label, scale, style_kwargs)
#               scale: multiply values by this before plotting
#   yticks  – optional (values, labels) for fixed tick labels

_CH_COLORS = plt.cm.tab10.colors   # one colour per channel

_CH_SNR_SERIES = [
    (f'nav.snr{i}', f'ch{i}', 0.01,
     {'lw': 0.8, 'alpha': 0.75, 'color': _CH_COLORS[i % len(_CH_COLORS)]})
    for i in range(8)
]

PANELS = [
    {
        'key': 'state',
        'title': 'Navigator state & waypoint index',
        'ylabel': '',
        'step': True,
        'series': [
            ('wpNav.state', 'state',  1.0, {'lw': 1.5, 'color': 'steelblue'}),
            ('wpNav.wpIdx', 'WP idx', 1.0, {'lw': 1.5, 'color': 'darkorange',
                                             'linestyle': '--'}),
        ],
        'yticks': (list(NAV_STATES.keys()),
                   [f"{k}: {v}" for k, v in NAV_STATES.items()]),
    },
    {
        'key': 'snr',
        'title': 'SNR — overall (max across channels)',
        'ylabel': 'SNR',
        'step': False,
        'series': [
            ('nav.snr', 'max SNR', 1.0, {'lw': 1.5, 'color': 'crimson'}),
        ],
    },
    {
        'key': 'snr_ch',
        'title': 'SNR — per channel (raw int16 / 100)',
        'ylabel': 'SNR',
        'step': False,
        'series': _CH_SNR_SERIES,
    },
    {
        'key': 'bearing',
        'title': 'Bearing & command yaw',
        'ylabel': 'degrees',
        'step': False,
        'series': [
            ('nav.bearing',         'smooth bearing', 1.0,
             {'lw': 1.5, 'color': 'steelblue'}),
            ('nav.cmdYaw',          'cmd yaw',        1.0,
             {'lw': 1.0, 'color': 'tomato', 'linestyle': '--'}),
            ('bearingCtrl.bearing', 'raw bearing',    1.0,
             {'lw': 0.8, 'color': 'grey', 'alpha': 0.6}),
        ],
    },
    {
        'key': 'grad_angle',
        'title': 'Gradient angle  (green = accepted, grey = rejected)',
        'ylabel': 'degrees',
        'step': False,
        'gradient_accept': 'angle',   # triggers split accepted/rejected rendering
        'series': [
            ('nav.gradAng', 'grad angle', 1.0,
             {'lw': 1.4, 'color': 'seagreen'}),
            ('nav.gradMag', 'grad magnitude', 1.0,
             {'lw': 1.2, 'color': 'mediumseagreen', 'linestyle': '--'}),
        ],
    },
    {
        'key': 'grad_r2',
        'title': 'Gradient quality — WLS plane-fit R²  (green = accepted)',
        'ylabel': 'R²',
        'step': False,
        'gradient_accept': 'r2',      # triggers threshold line + shading
        'series': [
            ('nav.gradR2', 'R²', 1.0,
             {'lw': 1.2, 'color': 'darkorange'}),
        ],
    },
    {
        'key': 'mapsize',
        'title': 'WLS map size',
        'ylabel': 'cells',
        'step': True,
        'series': [
            # wlsCtrl.mapSize is the current name; nav.mapSize kept for old logs
            ('wlsCtrl.mapSize', 'map cells', 1.0, {'lw': 1.2, 'color': 'teal'}),
            ('nav.mapSize',     'map cells (legacy)', 1.0,
             {'lw': 1.2, 'color': 'teal', 'linestyle': '--'}),
        ],
    },
    {
        'key': 'weights',
        'title': 'Fusion weights',
        'ylabel': 'weight',
        'step': False,
        'series': [
            ('nav.wB', 'w bearing',  1.0, {'lw': 1.2, 'color': 'steelblue'}),
            ('nav.wG', 'w gradient', 1.0, {'lw': 1.2, 'color': 'darkorange'}),
        ],
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Find the timestamp column (first column or explicit name)
    if 'timestamp_ms' in df.columns:
        ts_col = 'timestamp_ms'
    else:
        ts_col = df.columns[0]
    df['_t'] = (df[ts_col] - df[ts_col].iloc[0]) / 1000.0
    return df


def waypoint_transitions(df: pd.DataFrame):
    """Return list of (time_s, new_wp_index) where wpNav.wpIdx increases."""
    if 'wpNav.wpIdx' not in df.columns:
        return []
    idx = df['wpNav.wpIdx']
    mask = idx.ne(idx.shift()) & (df.index > 0)
    return list(zip(df.loc[mask, '_t'], df.loc[mask, 'wpNav.wpIdx']))


def gradient_accept_mask(df: pd.DataFrame) -> 'pd.Series':
    """
    Boolean mask: True on rows where the gradient was (likely) accepted.
    Mirrors the firmware conditions:  R² >= threshold  AND  mapSize >= min cells.
    Falls back gracefully if either column is missing.
    """
    mask = pd.Series(True, index=df.index)
    if 'nav.gradR2' in df.columns:
        mask &= df['nav.gradR2'] >= R2_ACCEPT_THRESHOLD
    if 'wlsCtrl.mapSize' in df.columns:
        mask &= df['wlsCtrl.mapSize'] >= MIN_MAP_CELLS
    return mask


def build_active_panels(df: pd.DataFrame, panel_keys=None):
    """Return only panels where at least one series column exists in df.

    If panel_keys is given, only panels whose 'key' is in panel_keys are
    considered (in the order they appear in PANELS, not panel_keys).
    """
    active = []
    for panel in PANELS:
        if panel_keys is not None and panel['key'] not in panel_keys:
            continue
        present = [s for s in panel['series'] if s[0] in df.columns]
        if present:
            active.append({**panel, 'series': present})
    return active


# ── Time-series figure ────────────────────────────────────────────────────────

def plot_timeseries(df: pd.DataFrame, title: str, panel_keys=None,
                    frac: float = None) -> 'plt.Figure | None':
    """Build the time-series panel figure. Returns None if no data.

    panel_keys: optional iterable of PANELS 'key' values to include
    (e.g. {'snr', 'snr_ch'}). If None, all panels with available data
    are shown.
    """
    active = build_active_panels(df, panel_keys)
    if not active:
        print("No recognised columns found in CSV — skipping time-series plot.")
        return None

    transitions = waypoint_transitions(df)
    t = df['_t']
    n = len(active)

    frac = frac or PAGE_FRAC
    fst.apply(frac * fst.TEXTWIDTH_IN, frac, tick=8, label=9, title=9,
              legend=8, suptitle=10)
    fig, ax_arr = plt.subplots(n, 1, figsize=(frac * fst.TEXTWIDTH_IN, 1.35 * n + 0.4),
                               sharex=True, layout='constrained')
    axes = [ax_arr] if n == 1 else list(ax_arr)
    if title:
        fig.suptitle(title, fontweight='bold')

    grad_mask = gradient_accept_mask(df)

    for ax, panel in zip(axes, active):
        ax.set_title(panel['title'], loc='left')
        ax.set_ylabel(panel['ylabel'])
        ax.grid(True, alpha=0.3)

        grad_accept = panel.get('gradient_accept')

        for col, lbl, scale, kw in panel['series']:
            vals = df[col] * scale
            if grad_accept == 'angle':
                ax.plot(t, vals.where(~grad_mask), color='#888888', lw=1.0,
                        linestyle='--', alpha=0.8, zorder=1)
                ax.plot(t, vals.where(grad_mask), label=f'{lbl} (accepted)',
                        zorder=2, **kw)
            elif panel.get('step'):
                ax.step(t, vals, where='post', label=lbl, **kw)
            else:
                ax.plot(t, vals, label=lbl, **kw)

        if grad_accept == 'r2':
            ax.axhline(R2_ACCEPT_THRESHOLD, color='seagreen', lw=1.0,
                       linestyle='--', alpha=0.9,
                       label=f'threshold ({R2_ACCEPT_THRESHOLD})')
            ax.fill_between(t, 0, 1, where=grad_mask.values,
                            transform=ax.get_xaxis_transform(),
                            color='seagreen', alpha=0.12, zorder=0,
                            label='accepted')

        if 'yticks' in panel:
            yv, yl = panel['yticks']
            seen = set()
            for col, *_ in panel['series']:
                if col in df.columns:
                    seen.update(int(v) for v in df[col].dropna().unique())
            fv = [v for v in yv if v in seen]
            fl = [yl[yv.index(v)] for v in fv]
            if fv:
                ax.set_yticks(fv)
                ax.set_yticklabels(fl, fontsize=fst.pt(8))

        for tx, wp_new in transitions:
            ax.axvline(tx, color='black', lw=0.8, linestyle=':', alpha=0.5)

        if len(panel['series']) > 1 or panel.get('gradient_accept'):
            ax.legend(loc='upper right', framealpha=0.7)

    if transitions:
        ax0 = axes[0]
        for tx, wp_new in transitions:
            ax0.annotate(f'WP {int(wp_new)}', xy=(tx, ax0.get_ylim()[1]),
                         xytext=(3, -12), textcoords='offset points',
                         fontsize=fst.pt(7), color='black', alpha=0.8)

    axes[-1].set_xlabel('Time (s)')
    return fig


# ── SNR heatmap figure ────────────────────────────────────────────────────────

def _build_snr_grid(x, y, snr, bin_m):
    pad = bin_m
    x_edges = np.arange(x.min() - pad, x.max() + pad + bin_m, bin_m)
    y_edges = np.arange(y.min() - pad, y.max() + pad + bin_m, bin_m)
    nx, ny = len(x_edges) - 1, len(y_edges) - 1
    grid = np.full((ny, nx), np.nan)
    xi = np.clip(np.floor((x - x_edges[0]) / bin_m).astype(int), 0, nx - 1)
    yi = np.clip(np.floor((y - y_edges[0]) / bin_m).astype(int), 0, ny - 1)
    for xi_i, yi_i, s in zip(xi, yi, snr):
        if np.isnan(grid[yi_i, xi_i]) or s > grid[yi_i, xi_i]:
            grid[yi_i, xi_i] = s
    return grid, x_edges, y_edges


def _build_snr_grid_mean(x, y, snr, bin_m):
    """Build SNR grid using mean per bin — better for survey/lawnmower maps."""
    pad = bin_m
    x_edges = np.arange(x.min() - pad, x.max() + pad + bin_m, bin_m)
    y_edges = np.arange(y.min() - pad, y.max() + pad + bin_m, bin_m)
    nx, ny = len(x_edges) - 1, len(y_edges) - 1
    grid_sum = np.zeros((ny, nx))
    grid_cnt = np.zeros((ny, nx), dtype=int)
    xi = np.clip(np.floor((x - x_edges[0]) / bin_m).astype(int), 0, nx - 1)
    yi = np.clip(np.floor((y - y_edges[0]) / bin_m).astype(int), 0, ny - 1)
    np.add.at(grid_sum, (yi, xi), snr)
    np.add.at(grid_cnt, (yi, xi), 1)
    with np.errstate(invalid='ignore'):
        grid = np.where(grid_cnt > 0, grid_sum / grid_cnt, np.nan)
    return grid, x_edges, y_edges


def _fill_nan_nearest(grid):
    """Fill NaN bins with the value of the nearest non-NaN bin."""
    nan_mask = np.isnan(grid)
    if not nan_mask.any():
        return grid
    try:
        from scipy.ndimage import distance_transform_edt
        # request indices only — avoids tuple-unpacking ambiguity
        idx = distance_transform_edt(nan_mask,
                                     return_distances=False,
                                     return_indices=True)
        return grid[tuple(idx)]
    except ImportError:
        pass

    # Pure-numpy fallback: repeatedly expand valid values one bin at a time
    filled = grid.copy()
    while True:
        still_nan = np.isnan(filled)
        if not still_nan.any():
            break
        pad = np.pad(filled, 1, constant_values=np.nan)
        neighbors = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1],
                               pad[1:-1, :-2], pad[1:-1, 2:]])
        fill_vals = np.nanmean(neighbors, axis=0)
        filled = np.where(still_nan & ~np.isnan(fill_vals), fill_vals, filled)
    return filled


def _smooth_grid(grid, sigma):
    """Gaussian smoothing on a fully-filled grid. Skips if scipy is not installed."""
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(grid, sigma=sigma)
    except ImportError:
        print("Warning: scipy not found — Gaussian smoothing skipped.")
        return grid


def _build_gradient_grid(x, y, grad_ang_deg, accepted, x_edges, y_edges):
    """
    Bin gradient angles (degrees) into the SNR heatmap grid using circular mean.
    Returns (xx, yy, (u_acc, v_acc, mask_acc), (u_rej, v_rej, mask_rej))
    where u/v are unit-length direction components.
    """
    nx, ny = len(x_edges) - 1, len(y_edges) - 1
    bin_w  = (x_edges[-1] - x_edges[0]) / nx
    bin_h  = (y_edges[-1] - y_edges[0]) / ny

    xi = np.clip(np.floor((x - x_edges[0]) / bin_w).astype(int), 0, nx - 1)
    yi = np.clip(np.floor((y - y_edges[0]) / bin_h).astype(int), 0, ny - 1)
    rad   = np.deg2rad(grad_ang_deg)
    sin_r = np.sin(rad)
    cos_r = np.cos(rad)
    flat  = yi * nx + xi

    out = []
    for mask in (accepted, ~accepted):
        sin_s = np.zeros(ny * nx)
        cos_s = np.zeros(ny * nx)
        cnt   = np.zeros(ny * nx, dtype=int)
        idx_k = flat[mask]
        np.add.at(sin_s, idx_k, sin_r[mask])
        np.add.at(cos_s, idx_k, cos_r[mask])
        np.add.at(cnt,   idx_k, 1)
        sin_s = sin_s.reshape(ny, nx)
        cos_s = cos_s.reshape(ny, nx)
        cnt   = cnt.reshape(ny, nx)
        has   = cnt > 0
        n     = np.where(has, cnt, 1)
        u     = cos_s / n
        v     = sin_s / n
        mag   = np.hypot(u, v)
        u     = np.where(has, u / np.where(mag > 0, mag, 1.0), np.nan)
        v     = np.where(has, v / np.where(mag > 0, mag, 1.0), np.nan)
        out.append((u, v, has))

    x_cent = (x_edges[:-1] + x_edges[1:]) / 2
    y_cent = (y_edges[:-1] + y_edges[1:]) / 2
    xx, yy = np.meshgrid(x_cent, y_cent)
    return xx, yy, out[0], out[1]


def _draw_wp_heatmap(ax, seg: pd.DataFrame, bin_m: float,
                     norm: mcolors.Normalize, cmap, wp_label: str,
                     show_gradient: bool = True, gradient_stride: int = 4,
                     obstacles: list = None, show_takeoff: bool = True):
    """Draw one waypoint's SNR heatmap into ax. Returns the pcolormesh artist."""
    x   = seg['stateEstimate.x'].to_numpy(dtype=float)
    y   = seg['stateEstimate.y'].to_numpy(dtype=float)
    snr = seg['nav.snr'].to_numpy(dtype=float)

    grid, x_edges, y_edges = _build_snr_grid(x, y, snr, bin_m)
    # Dark background so the gap between takeoff and a far-off beacon reads as
    # unvisited map area rather than an empty white void.
    ax.set_facecolor('#1a1a2e')
    mesh = ax.pcolormesh(x_edges, y_edges, grid, cmap=cmap, shading='flat',
                         norm=norm)

    # Flight path
    ax.plot(x, y, color='white', lw=0.8, alpha=0.5)

    # Takeoff cross (0, 0) — shown on every waypoint so the full flight path can
    # be placed relative to the origin.
    if show_takeoff:
        ax.plot(0, 0, marker='+', markersize=7, markeredgewidth=1.4,
                color='cyan', zorder=5)

    # ── Gradient angle overlay ────────────────────────────────────────────────
    if show_gradient and 'nav.gradAng' in seg.columns:
        ang   = seg['nav.gradAng'].to_numpy(dtype=float)
        valid = np.isfinite(ang)
        if valid.any():
            acc = np.ones(len(seg), dtype=bool)
            if 'nav.gradR2' in seg.columns:
                acc &= seg['nav.gradR2'].to_numpy(dtype=float) >= R2_ACCEPT_THRESHOLD
            if 'wlsCtrl.mapSize' in seg.columns:
                acc &= seg['wlsCtrl.mapSize'].to_numpy(dtype=float) >= MIN_MAP_CELLS

            xx, yy, (u_acc, v_acc, m_acc), (u_rej, v_rej, m_rej) = \
                _build_gradient_grid(x[valid], y[valid], ang[valid],
                                     acc[valid], x_edges, y_edges)

            s          = gradient_stride
            arrow_len  = bin_m * s * 0.8
            qkw        = dict(scale_units='xy', scale=1.0 / arrow_len,
                              width=0.003, headwidth=4, headlength=5, zorder=4,
                              angles='xy')
            xx_s, yy_s = xx[::s, ::s], yy[::s, ::s]

            for u_g, v_g, mask_g, color, alpha in [
                (u_rej[::s, ::s], v_rej[::s, ::s], m_rej[::s, ::s], '#aaaaaa', 0.55),
                (u_acc[::s, ::s], v_acc[::s, ::s], m_acc[::s, ::s], '#44ee88', 0.90),
            ]:
                m = mask_g & np.isfinite(u_g) & np.isfinite(v_g)
                if m.any():
                    ax.quiver(xx_s[m], yy_s[m], u_g[m], v_g[m],
                              color=color, alpha=alpha, **qkw)

    # Obstacle rectangles
    for i, (cx, cy, w, d) in enumerate(obstacles or []):
        rect = mpatches.Rectangle(
            (cx - w / 2, cy - d / 2), w, d,
            linewidth=2, edgecolor='white', facecolor='#555555',
            alpha=0.85, zorder=8,
            label='obstacle' if i == 0 else '_nolegend_')
        ax.add_patch(rect)
        ax.text(cx, cy, f'{w*100:.0f}×{d*100:.0f} cm',
                ha='center', va='center', fontsize=fst.pt(7), color='white', zorder=9)

    ax.set_title(wp_label, fontweight='bold')
    ax.set_xlabel('x  (m)')
    ax.set_ylabel('y  (m)')
    # 'box' shrinks the axes box to the data's aspect instead of padding the
    # data limits with empty space (waypoints have very different shapes).
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, color='white', alpha=0.08, linewidth=0.4)
    return mesh


def plot_snr_map(df: pd.DataFrame, title: str,
                 bin_m: float = SNR_MAP_BIN_M,
                 show_gradient: bool = True,
                 gradient_stride: int = 4,
                 obstacles: list = None,
                 frac: float = None) -> 'plt.Figure | None':
    """
    Build the 2-D SNR heatmap figure.
    When wpNav.wpIdx is present, one subplot is drawn per waypoint traversal
    so that the map reset between waypoints is reflected correctly.
    Gradient angle arrows are overlaid when show_gradient=True and nav.gradAng is logged.
    Returns None if position data is absent.
    """
    if not SNR_MAP_COLS.issubset(df.columns):
        return None
    data = df[df['nav.snr'] > 0].copy()
    if data.empty:
        print("Heatmap: no rows with nav.snr > 0, skipping.")
        return None

    cmap = plt.cm.plasma.copy()
    cmap.set_bad(color='#1a1a2e')

    # Shared colour scale across all subplots for fair visual comparison
    snr_all = data['nav.snr'].to_numpy(dtype=float)
    norm = mcolors.Normalize(vmin=snr_all.min(), vmax=snr_all.max())

    # Split into per-waypoint segments when index column is available
    if 'wpNav.wpIdx' in data.columns:
        segments = [(int(wp), grp)
                    for wp, grp in data.groupby('wpNav.wpIdx', sort=True)]
    else:
        segments = [(None, data)]

    n_wp = len(segments)
    # At most 2 columns so each map keeps room to breathe (3 waypoints become a
    # 2-top / 1-bottom grid rather than three cramped panels in a row).
    ncols = min(n_wp, 2)
    nrows = (n_wp + ncols - 1) // ncols

    frac = frac or PAGE_FRAC
    fst.apply(frac * fst.TEXTWIDTH_IN, frac, tick=8, label=9, title=9,
              legend=8, suptitle=10)
    fig_w = frac * fst.TEXTWIDTH_IN
    # Size the figure height to the data's own aspect so the equal-aspect maps
    # fill the panel instead of floating in dead space.
    _xr = data['stateEstimate.x']
    _yr = data['stateEstimate.y']
    _aspect = max(_yr.max() - _yr.min(), 0.1) / max(_xr.max() - _xr.min(), 0.1)
    _aspect = min(max(_aspect, 0.35), 2.2)
    fig_h = (fig_w / ncols) * _aspect * nrows * 0.82 + 1.0
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(fig_w, fig_h),
                             layout='constrained',
                             squeeze=False)

    # Hide any unused subplot slots
    for idx in range(n_wp, nrows * ncols):
        axes.flat[idx].set_visible(False)

    last_mesh = None
    for idx, (wp_idx, seg) in enumerate(segments):
        ax = axes.flat[idx]
        label = f'Waypoint {wp_idx}' if wp_idx is not None else 'All data'
        last_mesh = _draw_wp_heatmap(ax, seg, bin_m, norm, cmap, label,
                                     show_gradient=show_gradient,
                                     gradient_stride=gradient_stride,
                                     obstacles=obstacles)

    # Single shared colourbar on the right of the whole figure
    if last_mesh is not None:
        fig.colorbar(last_mesh, ax=axes, pad=0.02, label='SNR (max per bin)',
                     shrink=0.85)

    # Gradient legend (only when overlay is active and column present).
    # Placed just below the panels (outside the axes) so it never overlaps the
    # x-axis label of the bottom row.
    if show_gradient and 'nav.gradAng' in data.columns:
        acc_patch = mpatches.Patch(color='#44ee88', alpha=0.9, label='gradient (accepted)')
        rej_patch = mpatches.Patch(color='#aaaaaa', alpha=0.6, label='gradient (rejected)')
        fig.legend(handles=[acc_patch, rej_patch], loc='outside lower center',
                   ncol=2, framealpha=0.8)

    ts_str = ''
    if 'timestamp_ms' in df.columns:
        t0, t1 = df['timestamp_ms'].iloc[0], df['timestamp_ms'].iloc[-1]
        ts_str = f'  |  {(t1-t0)/1000:.1f} s'
    if title:
        fig.suptitle(f'{title}{ts_str}  —  bin {bin_m*100:.0f} cm',
                     fontweight='bold')

    return fig


# ── Survey / lawnmower heatmap ────────────────────────────────────────────────

def _parse_obstacles_from_filename(stem: str) -> list:
    """
    Extract obstacle(s) encoded in a data_gather filename.
    Format produced by data_gather_rect.py:
        _obs{cx:.2f}-{cy:.2f}m_{w*100:.0f}x{d*100:.0f}cm
    Returns list of (cx, cy, w_m, d_m) tuples.
    """
    return [
        (float(m.group(1)), float(m.group(2)),
         float(m.group(3)) / 100.0, float(m.group(4)) / 100.0)
        for m in re.finditer(
            r'obs([\d.]+)-([\d.]+)m_([\d.]+)x([\d.]+)cm', stem)
    ]


def plot_survey_map(df: pd.DataFrame, title: str,
                    bin_m: float = SNR_MAP_BIN_M,
                    lights: list = None,
                    sigma: float = 3.0,
                    obstacles: list = None,
                    frac: float = None) -> 'plt.Figure | None':
    """
    Side-by-side survey heatmap:
      Left  — raw mean-per-bin with flight path overlaid
      Right — nearest-neighbour filled + Gaussian smoothed, no flight path
    Both subplots share the same colour scale and show lights / obstacles.
    """
    if not SNR_MAP_COLS.issubset(df.columns):
        return None
    data = df[df['nav.snr'] > 0].copy()
    if data.empty:
        print("Survey map: no rows with nav.snr > 0, skipping.")
        return None

    x_all = data['stateEstimate.x'].to_numpy(dtype=float)
    y_all = data['stateEstimate.y'].to_numpy(dtype=float)
    snr   = data['nav.snr'].to_numpy(dtype=float)

    # Build raw grid (mean per bin, NaN where unvisited)
    grid_raw, x_edges, y_edges = _build_snr_grid_mean(x_all, y_all, snr, bin_m)

    # Build smoothed grid:
    #   1. Fill inter-pass NaN gaps with nearest-neighbour values
    #   2. Apply Gaussian for a smooth continuous appearance
    #   3. Rescale so the smoothed peak matches the raw peak — the Gaussian
    #      attenuates peaks proportionally, so a single scale factor restores
    #      the true intensity range without breaking the smooth look.
    grid_filled = _fill_nan_nearest(grid_raw)
    if sigma > 0:
        grid_smooth = _smooth_grid(grid_filled, sigma)
        raw_peak    = np.nanmax(grid_raw)
        smooth_peak = np.nanmax(grid_smooth)
        if smooth_peak > 0:
            grid_smooth = grid_smooth * (raw_peak / smooth_peak)
    else:
        grid_smooth = grid_filled

    # Shared colour scale across both panels
    vmin = np.nanmin(grid_raw)
    vmax = np.nanmax(grid_raw)
    cmap = plt.cm.plasma.copy()
    cmap.set_bad(color='#1a1a2e')
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    extent = [x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]]

    frac = frac or PAGE_FRAC
    fst.apply(frac * fst.TEXTWIDTH_IN, frac, tick=8, label=9, title=9,
              legend=8, suptitle=10)
    fig_w = frac * fst.TEXTWIDTH_IN
    fig, (ax_raw, ax_smooth) = plt.subplots(
        1, 2, figsize=(fig_w, fig_w * 6 / 15 + 0.3), layout='constrained')

    # ── Left: raw ────────────────────────────────────────────────────────────
    ax_raw.imshow(grid_raw, origin='lower', extent=extent,
                  cmap=cmap, norm=norm, interpolation='nearest', aspect='equal')
    ax_raw.plot(x_all, y_all, color='white', lw=0.6, alpha=0.5, label='flight path')
    ax_raw.set_title('Raw  (mean per bin)')

    # ── Right: smoothed ───────────────────────────────────────────────────────
    im = ax_smooth.imshow(grid_smooth, origin='lower', extent=extent,
                          cmap=cmap, norm=norm, interpolation='nearest', aspect='equal')
    sigma_str = f'σ={sigma} bins' if sigma > 0 else 'no smoothing'
    ax_smooth.set_title(f'Smoothed  ({sigma_str})')

    # Shared colourbar on the right
    fig.colorbar(im, ax=ax_smooth, label='SNR (mean per bin)')

    # ── Decorations on both axes ──────────────────────────────────────────────
    for ax in (ax_raw, ax_smooth):
        ax.plot(0, 0, marker='+', markersize=7, markeredgewidth=1.4,
                color='cyan', zorder=5, label='takeoff (0, 0)')

        for lx, ly in (lights or []):
            ax.plot(lx, ly, marker='*', markersize=11, markeredgewidth=1.0,
                    color='yellow', markeredgecolor='darkorange', zorder=10,
                    label=f'light  ({lx:.2f}, {ly:.2f}) m')

        for i, (cx, cy, w, d) in enumerate(obstacles or []):
            rect = mpatches.Rectangle(
                (cx - w / 2, cy - d / 2), w, d,
                linewidth=2, edgecolor='white', facecolor='#555555',
                alpha=0.85, zorder=8,
                label='obstacle' if i == 0 else '_nolegend_')
            ax.add_patch(rect)
            ax.text(cx, cy, f'{w*100:.0f}×{d*100:.0f} cm',
                    ha='center', va='center', fontsize=fst.pt(7), color='white', zorder=9)

        ax.set_xlabel('x  (m)')
        ax.set_ylabel('y  (m)')
        ax.grid(True, color='white', alpha=0.08, linewidth=0.4)

    # One shared, de-duplicated legend below both panels (the two maps mark the
    # same takeoff/light/obstacle, so a per-panel legend just repeated itself).
    handles, labels = ax_raw.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc='outside lower center',
                   ncol=len(handles), framealpha=0.8)

    ts_str = ''
    if 'timestamp_ms' in df.columns:
        t0, t1 = df['timestamp_ms'].iloc[0], df['timestamp_ms'].iloc[-1]
        ts_str = f'  |  {(t1-t0)/1000:.1f} s'
    if title:
        fig.suptitle(f'{title}{ts_str}  —  bin {bin_m*100:.0f} cm',
                     fontweight='bold')
    return fig


# ── Entry point ───────────────────────────────────────────────────────────────

def pick_from_runs() -> Path | None:
    """
    List all CSV files in the runs/ folder (relative to this script or cwd)
    and let the user pick one interactively.  Returns None if the folder is
    empty or doesn't exist.
    """
    # Search for a 'runs' folder next to this script, then in cwd
    candidates = [
        Path(__file__).parent.parent / 'runs',
        Path('runs'),
    ]
    runs_dir = next((p for p in candidates if p.is_dir()), None)
    if runs_dir is None:
        return None

    csvs = sorted(runs_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime,
                  reverse=True)
    if not csvs:
        print(f"No CSV files found in '{runs_dir}'.")
        return None

    print(f"\nCSV files in '{runs_dir}' (newest first):")
    for i, p in enumerate(csvs):
        print(f"  [{i}]  {p.name}")

    while True:
        try:
            choice = input(f"\nSelect file [0–{len(csvs)-1}] (Enter = 0): ").strip()
            idx = int(choice) if choice else 0
            if 0 <= idx < len(csvs):
                return csvs[idx]
            print(f"  Please enter a number between 0 and {len(csvs)-1}.")
        except (ValueError, EOFError):
            return csvs[0]


def main():
    parser = argparse.ArgumentParser(
        description='Plot a CrazyFlie navigation session CSV')
    parser.add_argument(
        'csv', nargs='?',
        help='Path to CSV file. Omit to pick from the runs/ folder, or falls '
             'back to navigate_session.csv in the current directory.')
    parser.add_argument(
        '--save', action='store_true',
        help='Save PNGs next to the CSV instead of showing interactively.')
    parser.add_argument(
        '--bin', type=float, default=SNR_MAP_BIN_M, metavar='M',
        help=f'Heatmap bin size in metres (default: {SNR_MAP_BIN_M} = 5 cm).')
    parser.add_argument(
        '--no-gradient', dest='show_gradient', action='store_false',
        help='Disable gradient angle arrows on the SNR heatmap.')
    parser.add_argument(
        '--gradient-stride', type=int, default=1, metavar='N',
        help='Show one gradient arrow per N bins (default: 1 = every 5 cm at 5 cm bins).')
    parser.add_argument(
        '--per-waypoint', dest='per_waypoint', action='store_true',
        help='Split time-series into one figure per waypoint traversal (time resets to 0 each).')
    parser.add_argument(
        '--survey', dest='survey', action='store_true', default=None,
        help='Survey/lawnmower mode: smooth heatmap, no flight path or gradient. '
             'Auto-detected when filename contains: ' + ', '.join(SURVEY_KEYWORDS) + '.')
    parser.add_argument(
        '--no-survey', dest='survey', action='store_false',
        help='Force navigation mode even if filename matches survey keywords.')
    parser.add_argument(
        '--light', nargs=2, type=float, metavar=('X', 'Y'), action='append',
        dest='lights',
        help='Mark a light source at (X, Y) metres on the survey heatmap. '
             'Can be given multiple times.')
    parser.add_argument(
        '--obstacle', nargs=4, type=float, metavar=('CX', 'CY', 'W', 'D'),
        action='append', dest='obstacles',
        help='Draw a rectangular obstacle: centre (CX, CY) m, size W×D m. '
             'Auto-parsed from filename when absent. Can be given multiple times.')
    parser.add_argument(
        '--smooth-sigma', type=float, default=3.0, metavar='S',
        help='Gaussian smoothing radius in bins for survey maps (default: 1.5). '
             'Set to 0 to disable.')
    parser.add_argument(
        '--panels', type=str, default=None, metavar='KEY1,KEY2,...',
        help='Comma-separated list of time-series panels to show '
             '(default: all available). Choices: '
             + ', '.join(p['key'] for p in PANELS) + '.')
    parser.add_argument(
        '--no-title', dest='no_title', action='store_true',
        help='Suppress the figure suptitle (the CSV filename header).')
    parser.add_argument(
        '--dpi', type=int, default=200, metavar='D',
        help='DPI for saved PNGs via --out-map/--out-ts (default: 200).')
    parser.add_argument(
        '--out-map', type=str, default=None, metavar='PATH',
        help='Save the SNR/survey map figure as a PNG to PATH (implies no interactive show).')
    parser.add_argument(
        '--out-ts', type=str, default=None, metavar='PATH',
        help='Save the time-series figure as a PNG to PATH (implies no interactive show).')
    parser.add_argument(
        '--waypoint', type=int, default=None, metavar='N',
        help='Restrict the data to a single wpNav.wpIdx value before plotting.')
    parser.add_argument(
        '--page-frac', type=float, default=1.0, metavar='F', dest='page_frac',
        help='On-page width as a fraction of \\textwidth (5 in). Figures are '
             'drawn at scale 1 so saved PNGs render at the right on-page size.')
    parser.set_defaults(show_gradient=True, per_waypoint=False)
    args = parser.parse_args()

    global PAGE_FRAC
    PAGE_FRAC = args.page_frac

    if args.csv:
        csv_path = Path(args.csv)
    else:
        csv_path = pick_from_runs() or Path('navigate_session.csv')

    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = load_csv(csv_path)
    print(f"Loaded {len(df)} rows from '{csv_path}'")
    print(f"Columns: {[c for c in df.columns if not c.startswith('_')]}")

    if args.waypoint is not None and 'wpNav.wpIdx' in df.columns:
        df = df[df['wpNav.wpIdx'] == args.waypoint].copy()
        print(f"Restricted to waypoint {args.waypoint}: {len(df)} rows")

    # Determine survey mode: explicit flag > auto-detect from filename
    if args.survey is None:
        is_survey = any(kw in csv_path.stem.lower() for kw in SURVEY_KEYWORDS)
    else:
        is_survey = args.survey
    lights = args.lights or []
    ttl = None if args.no_title else csv_path.name

    panel_keys = None
    if args.panels:
        valid_keys = {p['key'] for p in PANELS}
        panel_keys = {k.strip() for k in args.panels.split(',') if k.strip()}
        unknown = panel_keys - valid_keys
        if unknown:
            print(f"Error: unknown panel key(s): {', '.join(sorted(unknown))}\n"
                  f"Choices: {', '.join(sorted(valid_keys))}", file=sys.stderr)
            sys.exit(1)

    figures = []
    fig_ts = fig_map = None

    # Obstacles: explicit flag overrides auto-parse from filename
    auto_obs  = _parse_obstacles_from_filename(csv_path.stem)
    obstacles = args.obstacles if args.obstacles is not None else auto_obs

    if is_survey:
        fig_ts = plot_timeseries(df, title=ttl, panel_keys=panel_keys)
        if fig_ts is not None:
            figures.append(fig_ts)
        fig_map = plot_survey_map(df, title=ttl, bin_m=args.bin,
                                  lights=lights, sigma=args.smooth_sigma,
                                  obstacles=obstacles)
        if fig_map is not None:
            figures.append(fig_map)
    elif args.per_waypoint and 'wpNav.wpIdx' in df.columns:
        for wp_idx, seg in df.groupby('wpNav.wpIdx', sort=True):
            seg = seg.copy()
            seg['_t'] = seg['_t'] - seg['_t'].iloc[0]   # reset time to 0
            label = None if args.no_title else f"{csv_path.name} — Waypoint {int(wp_idx)}"
            fig_ts = plot_timeseries(seg, title=label, panel_keys=panel_keys)
            if fig_ts is not None:
                figures.append(fig_ts)
            fig_map = plot_snr_map(seg, title=label, bin_m=args.bin,
                                   show_gradient=args.show_gradient,
                                   gradient_stride=args.gradient_stride,
                                   obstacles=obstacles)
            if fig_map is not None:
                figures.append(fig_map)
    else:
        fig_ts = plot_timeseries(df, title=ttl, panel_keys=panel_keys)
        if fig_ts is not None:
            figures.append(fig_ts)
        fig_map = plot_snr_map(df, title=ttl, bin_m=args.bin,
                               show_gradient=args.show_gradient,
                               gradient_stride=args.gradient_stride,
                               obstacles=obstacles)
        if fig_map is not None:
            figures.append(fig_map)

    if not figures:
        print("Nothing to plot.")
        sys.exit(1)

    saved_named = False
    if args.out_ts and fig_ts is not None:
        fig_ts.savefig(args.out_ts, dpi=args.dpi)
        print(f"Saved: {args.out_ts}  (dpi {args.dpi})")
        saved_named = True
    if args.out_map and fig_map is not None:
        fig_map.savefig(args.out_map, dpi=args.dpi)
        print(f"Saved: {args.out_map}  (dpi {args.dpi})")
        saved_named = True

    if args.save:
        out = csv_path.with_suffix('.pdf')
        with PdfPages(out) as pdf:
            for fig in figures:
                pdf.savefig(fig, bbox_inches='tight')
        print(f"Saved: {out}  ({len(figures)} page{'s' if len(figures) > 1 else ''})")
    elif not saved_named:
        plt.show()


if __name__ == '__main__':
    main()
