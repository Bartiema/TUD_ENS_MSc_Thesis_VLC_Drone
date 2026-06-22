#!/usr/bin/env python3
"""
Illustrative figure for Chapter 3, Section "Why Existing Methods Fall Short":
the single-photodiode gradient method must MOVE to gather readings, and each
reading depends on the drone's HEADING, because one fixed sensor only sees the
source while it faces it.

The light field (from the built map) is the backdrop. A drone moves along a
short path and probes the field at three positions. At the middle position it has
rotated away from the source, so it reads low even though it is closer than the
first position -- the rotation corrupts the gradient the method infers.

This is an illustration drawn over real field data, not a logged run.

Usage:
    python scripts/single_pd_gradient_figure.py [out.png]
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyArrow

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures/single_pd_gradient.png"
MAP_CSV = "data/gradient_analysis/precomputed_map.csv"
LIGHT_X, LIGHT_Y = 5.1988, 5.329

df = pd.read_csv(MAP_CSV)
df = df[df["total_light"] > 0]
# Drop the dark saturation ring at the source so the field reads bright there.
_d = np.hypot(df["x"] - LIGHT_X, df["y"] - LIGHT_Y)
df = df[(_d > 0.95) | (df["total_light"] > 5500)]

fig, ax = plt.subplots(figsize=(8, 6.2))
cf = ax.tricontourf(df["x"], df["y"], df["total_light"], levels=20,
                    cmap="viridis", alpha=0.9)
cbar = fig.colorbar(cf, ax=ax, shrink=0.85)
cbar.set_label("Light strength")

ax.scatter([LIGHT_X], [LIGHT_Y], marker="*", s=340, c="gold",
           edgecolors="black", linewidths=0.8, zorder=6, label="Light source")


def source_angle(x, y):
    return np.degrees(np.arctan2(LIGHT_Y - y, LIGHT_X - x))


def draw_probe(x, y, heading_deg, label, lbl_dxy=(10, -18),
               note=None, note_dxy=(0, 0)):
    """Draw the drone, its single-sensor field of view, and its reading label."""
    fov = 80.0
    ax.add_patch(Wedge((x, y), 0.85, heading_deg - fov / 2, heading_deg + fov / 2,
                       facecolor="white", edgecolor="black", alpha=0.30,
                       lw=0.8, zorder=4))
    hr = np.radians(heading_deg)
    ax.add_patch(FancyArrow(x, y, 0.7 * np.cos(hr), 0.7 * np.sin(hr),
                            width=0.03, head_width=0.18, head_length=0.18,
                            length_includes_head=True, color="black", zorder=5))
    ax.scatter([x], [y], s=120, c="white", edgecolors="black",
               linewidths=1.2, zorder=5)
    ax.annotate(label, (x, y), textcoords="offset points", xytext=lbl_dxy,
                fontsize=10, fontweight="bold", color="black", zorder=7)
    if note:
        ax.annotate(note, (x, y), textcoords="offset points", xytext=note_dxy,
                    fontsize=9, color="#b3122b", fontweight="bold", zorder=7,
                    ha="center")


# Three probe positions along a path toward the source.
p1 = (1.4, 0.9)
p2 = (2.8, 2.1)
p3 = (3.8, 3.1)

# Motion path (dashed) -- the drone must travel to gather successive readings.
px, py = zip(p1, p2, p3)
ax.plot(px, py, ls="--", color="black", lw=1.6, zorder=3)
ax.annotate("the drone must move\nto gather readings", (0.2, 3.6),
            fontsize=9, style="italic", color="black", ha="left", zorder=7)

# P1 and P3 face the source; P2 has rotated away.
draw_probe(*p1, source_angle(*p1), "$S_1$: faces source", lbl_dxy=(10, -18))
draw_probe(*p2, source_angle(*p2) + 150, "$S_2$", lbl_dxy=(-22, 4),
           note="rotated away:\nreads low though closer", note_dxy=(96, -2))
draw_probe(*p3, source_angle(*p3), "$S_3$: faces source", lbl_dxy=(12, -2))

ax.set_xlim(-0.3, 6.4)
ax.set_ylim(-0.3, 6.2)
ax.set_xlabel("X position (m)")
ax.set_ylabel("Y position (m)")
ax.set_aspect("equal")
ax.set_title("Single-photodiode gradient: sampling by motion and orientation")
ax.legend(loc="lower right", fontsize=9)
fig.tight_layout()
fig.savefig(OUT, dpi=300, bbox_inches="tight")
print(f"Saved -> {OUT}")
