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

Thesis figures (page-accurate text via figstyle, see scripts/figstyle.py):
    python visualize_setup.py --page-frac 0.50 \
        --out figures/real_life_setup_plot_no_obstacle.png
    python visualize_setup.py --obstacle --page-frac 0.60 \
        --out figures/real_life_setup_plot_with_obstacle.png
"""

import argparse
import math
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as fs

# Native canvas size. Near-square to match the (equal-aspect) content so the
# saved PNG needs no tight crop -- which would change its width and break the
# figstyle scale math. figstyle.apply() enlarges only the text so it stays
# readable after LaTeX scales the figure down to its on-page width.
FIG_W = 7.0
FIG_H = 6.0

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
#   label             text shown next to the light (kept short; the legend
#                     already says "Light source")
#   label_dx/dy       label offset from the star (metres)
#   label_ha/va       label anchor (default centred above the star)
LIGHTS = [
    # 170 Hz beacon (top-right): label to the star's right so it stays clear of
    # the top-left legend (which is widest at small page fractions).
    dict(pos=(2.90, 1.80), direction=240, cone=35, reach=3.0, label='170 Hz',
         label_dx=0.12, label_dy=0.0, label_ha='left', label_va='center'),
    # 150 Hz beacon (far-right edge): anchor the label to the star's left so it
    # does not spill past the right axis.
    dict(pos=(3.2, 0.20), direction=180, cone=35, reach=3.0, label='150 Hz',
         label_dx=0.05, label_dy=0.08, label_ha='right', label_va='bottom'),
]

# Obstacles — rectangular columns:
#   cx, cy    centre position (metres)
#   w         width along x-axis (metres)
#   d         depth along y-axis (metres)
#   label     optional text inside the box
OBSTACLES = [
    # dict(cx=2.15, cy=0.80, w=0.20, d=0.25, label='Obstacle'),
]

# Obstacle drawn when --obstacle is passed (Chapter 6 obstacle experiment).
# Same box used in the real obstacle flights: set into the route to the beacon
# and a little to one side.
OBSTACLE = dict(cx=2.15, cy=0.80, w=0.20, d=0.25, label='Obstacle')

# ══════════════════════════════════════════════════════════════════════════════


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_light(ax, pos, direction_deg, cone_deg, reach, label,
                label_dx=0.0, label_dy=0.10, label_ha='center', label_va='bottom'):
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

    # Label — placement controlled per-light so it stays inside the axes and
    # clear of the legend (see the LIGHTS dict).
    ax.text(x + label_dx, y + label_dy, label, ha=label_ha, va=label_va,
            fontsize=fs.pt(9), color='darkorange', fontweight='bold', zorder=6)


def _draw_obstacle(ax, cx, cy, w, d, label):
    """Draw a rectangular obstacle with a size label."""
    rect = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - d / 2), w, d,
        boxstyle='square,pad=0', linewidth=2,
        edgecolor='#cccccc', facecolor='#444444', zorder=4)
    ax.add_patch(rect)
    if label:
        ax.text(cx, cy + d / 2 + 0.04, label,
                ha='center', va='bottom', fontsize=fs.pt(8),
                color='#cccccc', zorder=5)
    ax.text(cx, cy, f'{w*100:.0f}×{d*100:.0f} cm',
            ha='center', va='center', fontsize=fs.pt(7),
            color='white', zorder=5)


def _draw_takeoff(ax, pos):
    """Draw the takeoff / origin marker."""
    x, y = pos
    ax.plot(x, y, marker='+', markersize=18, markeredgewidth=2.5,
            color='cyan', zorder=5, label='Takeoff / origin')
    ax.text(x + 0.06, y + 0.06, f'({x:.2f}, {y:.2f})',
            fontsize=fs.pt(8), color='cyan', zorder=6)


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
                ha='center', fontsize=fs.pt(8), color='#888888',
                arrowprops=None)
    ax.annotate(f"{area['y_max'] - area['y_min']:.1f} m",
                xy=(area['x_min'], ym), xytext=(area['x_min'] - 0.22, ym),
                ha='right', va='center', fontsize=fs.pt(8), color='#888888',
                rotation=90)


# ── Main figure ───────────────────────────────────────────────────────────────

def build_figure(area=AREA, takeoff=TAKEOFF,
                 lights=None, obstacles=None, frac=0.5) -> plt.Figure:
    lights    = lights    or LIGHTS
    obstacles = obstacles if obstacles is not None else OBSTACLES

    # Enlarge text so it reads at ~8-9 pt once LaTeX scales the figure to its
    # on-page width (frac * textwidth). Composition is unchanged.
    fs.apply(FIG_W, frac)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), layout='constrained')
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
                    light['cone'], light['reach'], light.get('label', ''),
                    label_dx=light.get('label_dx', 0.0),
                    label_dy=light.get('label_dy', 0.10),
                    label_ha=light.get('label_ha', 'center'),
                    label_va=light.get('label_va', 'bottom'))

    # Legend proxy artists — only the two markers. The obstacle box is labelled
    # in-plot and the light cone is self-evident, so leaving them out keeps the
    # legend small enough to sit in the top-left corner without crowding.
    legend_handles = [
        mlines.Line2D([], [], marker='*', color='yellow', markeredgecolor='darkorange',
                      markersize=12, linewidth=0, label='Light source'),
        mlines.Line2D([], [], marker='+', color='cyan', markersize=12,
                      markeredgewidth=2, linewidth=0, label='Takeoff / origin'),
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=fs.pt(8),
              framealpha=0.6, facecolor='#1a1a2e', labelcolor='white')

    ax.set_xlabel('x  (m) — forward', fontsize=fs.pt(9), color='white')
    ax.set_ylabel('y  (m) — left',    fontsize=fs.pt(9), color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#555555')

    # A little extra headroom at the top so the above-beacon labels are not
    # clipped against the axis frame (only when limits are auto-fit).
    if not area:
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.set_xlim(x0, x1 + 0.45)
        ax.set_ylim(y0, y1 + 0.30)

    ax.set_aspect('equal')
    # No suptitle: the LaTeX caption describes the figure (thesis convention),
    # and a large scaled title would clip on the narrow on-page slot.
    return fig


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Visualise the drone flight setup')
    parser.add_argument('--save', action='store_true',
                        help='Save as setup.pdf next to this script.')
    parser.add_argument('--obstacle', action='store_true',
                        help='Draw the Chapter 6 obstacle box.')
    parser.add_argument('--page-frac', type=float, default=0.5, dest='page_frac',
                        help='On-page width as a fraction of \\textwidth '
                             '(controls text scaling; default 0.5).')
    parser.add_argument('--out', default=None, metavar='FILE.png',
                        help='Save a page-accurate PNG to this path.')
    args = parser.parse_args()

    obstacles = [OBSTACLE] if args.obstacle else []
    fig = build_figure(obstacles=obstacles, frac=args.page_frac)

    if args.out:
        fs.save(fig, args.out, dpi=300, facecolor=fig.get_facecolor())
    elif args.save:
        out = Path(__file__).parent / 'setup.pdf'
        fig.savefig(out, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Saved: {out}")
    else:
        plt.show()


if __name__ == '__main__':
    main()
