#!/usr/bin/env python3
"""
Render the built light-intensity map as a smooth top-down field for Chapter 3
(Section "Light Intensity Map").

Uses the same drawing method as the gradient-method comparison figure
(gradient_fitting_analyzer.py in the simulator repo): a filled tri-contour of the
scattered map samples, with the light source and the obstacle drawn for context.

Reads a precomputed map CSV with columns: grid_x, grid_y, x, y, total_light, ...
Cells that read zero (sensor saturation directly under the lamp, and the pillar's
shadow) are dropped so the contour interpolates smoothly across them.

Usage:
    python scripts/light_map_figure.py [csv] [out.png]
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as fst

DEFAULT_CSV = "data/gradient_analysis/precomputed_map.csv"
DEFAULT_OUT = "figures/gradient_analysis/light_map.png"

# Scene geometry -- matches the simulator world and the comparison figure.
LIGHT_X, LIGHT_Y = 5.1988, 5.329
OBSTACLE_X, OBSTACLE_Y = 0.8, 1.5
OBSTACLE_R = 0.4
CLEARANCE_R = OBSTACLE_R + 0.5   # safety circle the drone keeps clear


def main():
    csv = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

    df = pd.read_csv(csv)
    df = df[df["total_light"] > 0]          # drop saturation/shadow holes

    # Included at 0.72\textwidth -> 3.6 in. Scale 1: the PNG is the page result.
    fst.apply(3.6, frac=0.72, tick=8, label=9, title=9, legend=8)
    fig, ax = plt.subplots(figsize=(3.6, 3.4))

    cf = ax.tricontourf(df["x"], df["y"], df["total_light"],
                        levels=20, cmap="viridis")
    cbar = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("Recorded light strength")

    # Light source.
    ax.scatter([LIGHT_X], [LIGHT_Y], marker="*", s=90, c="gold",
               edgecolors="black", linewidths=0.8, zorder=5, label="Light source")

    # Obstacle (physical pillar) and the clearance circle the drone keeps.
    ax.add_patch(Circle((OBSTACLE_X, OBSTACLE_Y), OBSTACLE_R,
                        facecolor="0.6", edgecolor="black", linewidth=1.2,
                        zorder=4, label="Obstacle"))
    ax.add_patch(Circle((OBSTACLE_X, OBSTACLE_Y), CLEARANCE_R,
                        facecolor="none", edgecolor="black", linewidth=1.0,
                        linestyle="--", zorder=4, label="Clearance"))

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_title("Built light-intensity map (top view)")
    ax.set_aspect("equal")
    ax.legend(loc="upper left", framealpha=0.85)
    fig.tight_layout()
    fst.save(fig, out)


if __name__ == "__main__":
    main()
