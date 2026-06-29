#!/usr/bin/env python3
"""Shared figure style + font sizing for the thesis figures.

Goal
----
Keep every figure's existing size and composition, but make the *rendered*
on-page text large enough to read: the smallest text should land at ~9 pt next
to the thesis's 10 pt body text (``documentclass[10pt]``, ``\\textwidth = 5 in``).

How rendered size works
-----------------------
A figure saved at ``fig_w`` inches and included with ``width=frac\\textwidth``
is scaled by LaTeX by ``scale = frac*5 / fig_w``. A matplotlib font of ``F`` pt
therefore renders on the page at ``F * scale`` pt. To render at a target ``t``
pt we set the matplotlib font to ``t / scale``.

:func:`apply` computes that scale from the figure's *own* width and the on-page
fraction, then sets the rcParams font hierarchy to the desired rendered sizes.
Use :func:`pt` for any explicit per-call ``fontsize`` (annotations, etc.).

Two rules keep the math honest:
  1. Keep the script's real ``figsize`` width and pass it to :func:`apply`.
  2. Never save with ``bbox_inches='tight'`` -- it re-crops to the content and
     changes the saved width, breaking the scale. Use :func:`save`.
"""

import os
import matplotlib as mpl

TEXTWIDTH_IN = 5.0          # \textwidth in thesis.tex
BODY_PT = 10.0              # documentclass[10pt]

# Default rendered-pt hierarchy (what you want to SEE on the page).
# Calibrated so in-plot annotations (~7 pt, set per-call via pt(7)) read like the
# 10 pt body text; axis labels a touch larger, titles larger still.
R_TICK = 8.0
R_LABEL = 9.0
R_LEGEND = 8.0
R_TITLE = 11.0
R_SUPTITLE = 11.0
R_ANNOT = 7.0       # in-plot annotation text; use fs.pt(fs.R_ANNOT)

# Shared palette
BLUE = "#1f3b73"
RED = "#d1495b"
TEAL = "#2a9d8f"
GOLD = "#e9c46a"
GREY = "#6c757d"

_scale = 1.0


def page_scale(fig_w_in, frac):
    """LaTeX scale factor applied to a ``fig_w_in`` figure at ``frac`` width."""
    return (frac * TEXTWIDTH_IN) / fig_w_in


def pt(rendered_pt):
    """matplotlib fontsize that renders at ``rendered_pt`` given the last apply()."""
    return rendered_pt / _scale


def figsize(frac, aspect=4 / 3, height_in=None):
    """Convenience: a figure exactly ``frac\\textwidth`` wide (scale == 1)."""
    w = frac * TEXTWIDTH_IN
    h = height_in if height_in is not None else w / aspect
    return (w, h)


def apply(fig_w_in, frac, tick=R_TICK, label=R_LABEL, legend=R_LEGEND,
          title=R_TITLE, suptitle=R_SUPTITLE):
    """Set rcParams so text renders at the given on-page pt sizes.

    fig_w_in: the figure's real width in inches (figsize[0]).
    frac:     on-page include width as a fraction of \\textwidth.
    The remaining args are desired *rendered* pt sizes.
    """
    global _scale
    _scale = page_scale(fig_w_in, frac)
    mpl.rcParams.update({
        "font.size": label / _scale,
        "axes.titlesize": title / _scale,
        "axes.labelsize": label / _scale,
        "xtick.labelsize": tick / _scale,
        "ytick.labelsize": tick / _scale,
        "legend.fontsize": legend / _scale,
        "legend.title_fontsize": legend / _scale,
        "figure.titlesize": suptitle / _scale,
        "savefig.dpi": 300,
        "figure.dpi": 120,
        "savefig.bbox": "standard",  # never 'tight'
    })
    return _scale


def save(fig, out, **kwargs):
    """Save without 'tight' bbox so the saved width stays exact."""
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    kwargs.pop("bbox_inches", None)
    fig.savefig(out, **kwargs)
    print(f"Saved -> {out}")
