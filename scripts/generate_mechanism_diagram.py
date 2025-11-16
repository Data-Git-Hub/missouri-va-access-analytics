#!/usr/bin/env python3
"""
generate_mechanism_diagram.py

Creates a mechanism / pipeline diagram illustrating the ML workflow
for the Missouri VA access project.

Output:
    C:/Projects/missouri-va-access-analytics/figures/mech_diag.png
"""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---------- Output path ----------
OUT_PATH = Path(r"C:/Projects/missouri-va-access-analytics/figures")
OUT_PATH.mkdir(parents=True, exist_ok=True)
FNAME = OUT_PATH / "mech_diag.png"


def add_box(ax, x, y, width, height, text, box_color="#E0E0E0"):
    """Draw a rounded box with centered text and return its center + width."""
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.25,rounding_size=0.15",
        linewidth=1.5,
        edgecolor="black",
        facecolor=box_color,
    )
    ax.add_patch(box)

    ax.text(
        x + width / 2.0,
        y + height / 2.0,
        text,
        ha="center",
        va="center",
        fontsize=8.5,      # slightly smaller
        wrap=True,
    )

    return (x + width / 2.0, y + height / 2.0), width


def add_arrow(ax, start_center, start_w, end_center, end_w):
    """Draw an arrow from the right edge of one box to the left edge of the next."""
    sx = start_center[0] + start_w / 2.0 - 0.05
    sy = start_center[1]
    ex = end_center[0] - end_w / 2.0 + 0.05
    ey = end_center[1]

    ax.annotate(
        "",
        xy=(ex, ey),
        xytext=(sx, sy),
        arrowprops=dict(arrowstyle="->", lw=1.5),
    )


def main():
    # ---------- Figure ----------
    fig, ax = plt.subplots(figsize=(12, 3.2))  # a bit wider and taller
    ax.axis("off")

    # Labels with manual line breaks to prevent bleed
    labels = [
        "Raw MO Subset\n(Griffith 2024)",
        "Cleaning & Validation\n(schema, types, logic)",
        "Feature Engineering\n(one-hot,\nscaling,\nfilters)",
        "Train/Test Split\n(stratified 80/20)",
        "ML Models\n(LogReg +\nRandom Forest)",
        "Evaluation & Reporting\n(AUC,\nconfusion matrix,\nfeature importance,\nEDA)",
    ]

    # Box widths (last one widest)
    widths = [2.4, 2.8, 2.8, 2.6, 2.6, 3.8]
    height = 1.25
    y = 1.0
    gap = 0.6

    centers = []
    used_widths = []

    x = 0.0
    for label, w in zip(labels, widths):
        center, w_used = add_box(ax, x, y, w, height, label)
        centers.append(center)
        used_widths.append(w_used)
        x += w + gap

    total_width = x - gap

    # ---------- Arrows ----------
    for i in range(len(centers) - 1):
        add_arrow(ax, centers[i], used_widths[i], centers[i + 1], used_widths[i + 1])

    # Frame everything
    ax.set_xlim(-0.5, total_width + 0.5)
    ax.set_ylim(0.5, 3.0)

    plt.tight_layout()
    plt.savefig(FNAME, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Saved mechanism diagram to: {FNAME.resolve()}")


if __name__ == "__main__":
    main()
