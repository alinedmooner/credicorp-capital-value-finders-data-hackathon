"""Shared presentation chart styling."""

import sys
from pathlib import Path

import matplotlib as mpl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brand import GRID, NAVY, ORANGE, SERIES, TEXT, TEXT_MUTED, WHITE


def configure():
    mpl.rcParams.update({
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titleweight": "bold",
        "axes.titlecolor": NAVY,
        "axes.labelcolor": TEXT,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "grid.alpha": 0.85,
        "legend.frameon": False,
        "legend.labelcolor": TEXT,
    })


def style_axis(ax, *, grid_axis="both"):
    ax.grid(True, axis=grid_axis, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_note(fig, text):
    fig.text(0.08, 0.025, text, color=TEXT_MUTED, fontsize=9, ha="left")
