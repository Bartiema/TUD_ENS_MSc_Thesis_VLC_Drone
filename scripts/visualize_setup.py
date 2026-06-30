"""
visualize_setup.py
Top-down 2-D diagram of the flight setup:
  - Room / survey area boundary
  - Light source(s) with illumination cone and direction
  - Takeoff position
  - Rectangular obstacles

Edit the SETUP section below, then:
    python visualize_setup.py
    python visualize_setup.py --save        # saves setup.pdf next to this script
"""

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
#  SETUP — edit this section to match your physical arrangement
# ══════════════════════════════════════════════════════════════════════════════

# Room / flyable area boundary (metres, from takeoff origin).
# Set to None to auto-fit around all placed objects.
# AREA = dict(x_min=-0.3, x_max=3.3, y_min=-0.3, y_max=1.8)
AREA = None

# Takeoff position (metres).
TAKEOFF = (0.0, 0.0)

# Lights — list of dicts:
#   pos       (x, y)  position in metres
#   direction         angle the light *points* in degrees
#                     (0 = +x / east, 90 = +y / north, 180 = -x / west …)
#   cone              half-angle of the beam in degrees  (e.g. 40 → 80° total)
#   reach             visual length of the cone (metres)
#   label             text shown next to the light
LIGHTS = [
    dict(pos=(2.90, 1.80), direction=240, cone=35, reach=3.0, label='Light  170 Hz'),
    dict(pos=(3.2, 0.20), direction=180, cone=35, reach=3.0, label='Light  150 Hz'),
]

# Obstacles — rectangular columns:
#   cx, cy    centre position (metres)
#   w         width along x-axis (metres)
#   d         depth along y-axis (metres)
#   label     optional text inside the box
OBSTACLES = [
    # dict(cx=2.15, cy=0.80, w=0.20, d=0.25, label='Obstacle'),
]

# ══════════════════════════════════════════════════════════════════════════════


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_light(ax, pos, direction_deg, cone_deg, reach, label):
    """Draw a light source: star marker, filled cone, centre-line, label."""
    x, y = pos
    dir_rad  = math.radians(direction_deg)
    half_rad = math.radians(cone_deg)

    # Filled cone (Wedge uses degrees, CCW from +x)
    wedge = mpatches.Wedge(
        (x, y), reach,
        theta1=math.degrees(dir_rad - half_rad),
        theta2=math.degrees(dir_rad + half_rad),
        facecolor='yellow', alpha=0.15, edgecolor='none', zorder=2)
    ax.add_patch(wedge)

    # Cone outline edges
    for sign in (-1, +1):
        ang = dir_rad + sign * half_rad
        ax.plot([x, x + reach * math.cos(ang)],
                [y, y + reach * math.sin(ang)],
                color='gold', lw=1.0, linestyle='--', alpha=0.6, zorder=3)

    # Centre direction line
    ax.annotate('', xy=(x + reach * math.cos(dir_rad),
                        y + reach * math.sin(dir_rad)),
                xytext=(x, y),
                arrowprops=dict(arrowstyle='->', color='orange',
                                lw=1.8, mutation_scale=16),
                zorder=4)

    # Light marker
    ax.plot(x, y, marker='*', markersize=20, markeredgewidth=1.2,
            color='yellow', markeredgecolor='darkorange', zorder=5)

    # Label
    ax.text(x, y + 0.07, label, ha='center', va='bottom',
            fontsize=9, color='darkorange', fontweight='bold', zorder=6)


def _draw_obstacle(ax, cx, cy, w, d, label):
    """Draw a rectangular obstacle with a size label."""
    rect = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - d / 2), w, d,
        boxstyle='square,pad=0', linewidth=2,
        edgecolor='#cccccc', facecolor='#444444', zorder=4)
    ax.add_patch(rect)
    if label:
        ax.text(cx, cy + d / 2 + 0.04, label,
                ha='center', va='bottom', fontsize=8,
                color='#cccccc', zorder=5)
    ax.text(cx, cy, f'{w*100:.0f}×{d*100:.0f} cm',
            ha='center', va='center', fontsize=7,
            color='white', zorder=5)


def _draw_takeoff(ax, pos):
    """Draw the takeoff / origin marker."""
    x, y = pos
    ax.plot(x, y, marker='+', markersize=18, markeredgewidth=2.5,
            color='cyan', zorder=5, label='Takeoff / origin')
    ax.text(x + 0.06, y + 0.06, f'({x:.2f}, {y:.2f})',
            fontsize=8, color='cyan', zorder=6)


def _draw_area(ax, area):
    """Draw the room / survey boundary."""
    rect = mpatches.Rectangle(
        (area['x_min'], area['y_min']),
        area['x_max'] - area['x_min'],
        area['y_max'] - area['y_min'],
        linewidth=1.5, edgecolor='#888888', facecolor='#0d0d1a',
        linestyle='--', zorder=0)
    ax.add_patch(rect)
    # Dimension annotations
    xm = (area['x_min'] + area['x_max']) / 2
    ym = (area['y_min'] + area['y_max']) / 2
    ax.annotate(f"{area['x_max'] - area['x_min']:.1f} m",
                xy=(xm, area['y_min']), xytext=(xm, area['y_min'] - 0.18),
                ha='center', fontsize=8, color='#888888',
                arrowprops=None)
    ax.annotate(f"{area['y_max'] - area['y_min']:.1f} m",
                xy=(area['x_min'], ym), xytext=(area['x_min'] - 0.22, ym),
                ha='right', va='center', fontsize=8, color='#888888',
                rotation=90)


# ── Main figure ───────────────────────────────────────────────────────────────

def build_figure(area=AREA, takeoff=TAKEOFF,
                 lights=None, obstacles=None) -> plt.Figure:
    lights    = lights    or LIGHTS
    obstacles = obstacles or OBSTACLES

    fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
    fig.patch.set_facecolor('#0d0d1a')
    ax.set_facecolor('#12122a')

    # Grid
    ax.grid(True, color='#2a2a4a', linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)

    # Area boundary
    if area:
        _draw_area(ax, area)
        pad = 0.4
        ax.set_xlim(area['x_min'] - pad, area['x_max'] + pad)
        ax.set_ylim(area['y_min'] - pad, area['y_max'] + pad)

    # Takeoff
    _draw_takeoff(ax, takeoff)

    # Obstacles
    for obs in obstacles:
        _draw_obstacle(ax, obs['cx'], obs['cy'], obs['w'], obs['d'],
                       obs.get('label', ''))

    # Lights
    for light in lights:
        _draw_light(ax, light['pos'], light['direction'],
                    light['cone'], light['reach'], light.get('label', ''))

    # Legend proxy artists
    legend_handles = [
        mlines.Line2D([], [], marker='*', color='yellow', markeredgecolor='darkorange',
                      markersize=12, linewidth=0, label='Light source'),
        mlines.Line2D([], [], marker='+', color='cyan', markersize=12,
                      markeredgewidth=2, linewidth=0, label='Takeoff / origin'),
        mpatches.Patch(facecolor='#444444', edgecolor='#cccccc',
                       linewidth=1.5, label='Obstacle'),
        mpatches.Patch(facecolor='yellow', alpha=0.2, edgecolor='gold',
                       linestyle='--', label='Light cone'),
    ]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=9,
              framealpha=0.6, facecolor='#1a1a2e', labelcolor='white')

    ax.set_xlabel('x  (m) — forward', fontsize=10, color='white')
    ax.set_ylabel('y  (m) — left',    fontsize=10, color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#555555')

    ax.set_aspect('equal')
    fig.suptitle('Flight setup — top-down view', fontsize=13,
                 fontweight='bold', color='white')
    return fig


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Visualise the drone flight setup')
    parser.add_argument('--save', action='store_true',
                        help='Save as setup.pdf next to this script.')
    args = parser.parse_args()

    fig = build_figure()

    if args.save:
        out = Path(__file__).parent / 'setup.pdf'
        fig.savefig(out, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {out}")
    else:
        plt.show()


if __name__ == '__main__':
    main()
