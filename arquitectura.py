"""Render the data-flow architecture diagram."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from brand import GRID, NAVY, ORANGE, TEXT, TEXT_MUTED, WHITE


STAGES = [
    {
        "id": "rstudio",
        "name": "Limpieza y procesamiento",
        "tools": "R / RStudio\nUso principal: vistazo rápido\ninicial",
        "machine": "Máquina A · PC de un compañero",
        "status": "Fuera del repositorio",
        "versioned": False,
        "x": 0.75,
        "y": 2.0,
        "width": 2.75,
        "height": 4.15,
    },
    {
        "id": "analysis",
        "name": "Transformación y análisis",
        "tools": "Visual Studio Code + GitHub Copilot\nPython: pandas y numpy",
        "machine": "Máquina B · PC de otro compañero",
        "status": "Versionado en el repositorio",
        "versioned": True,
        "x": 5.10,
        "y": 2.0,
        "width": 3.15,
        "height": 4.15,
    },
    {
        "id": "reporting",
        "name": "Visualización y reporte",
        "tools": "Python: pandas, matplotlib y rich",
        "machine": "Esta máquina",
        "status": "Versionado en el repositorio",
        "versioned": True,
        "x": 9.45,
        "y": 2.0,
        "width": 3.00,
        "height": 4.15,
    },
]

HANDOFF = {
    "label": "Artefacto de entrega\nserialized/\n7 archivos\nCSV limpios",
    "x": 3.73,
    "y": 3.77,
    "width": 1.05,
    "height": 1.45,
}

REPOSITORY = {
    "label": "Repositorio\nGitHub\nConvergencia de\netapas 2 y 3",
    "x": 13.35,
    "y": 3.05,
    "width": 1.75,
    "height": 2.10,
}

LANES = [
    (0.45, 4.05, "MÁQUINA A", "PC de un compañero"),
    (4.05, 8.95, "MÁQUINA B", "PC de otro compañero"),
    (8.95, 12.95, "ESTA MÁQUINA", "Visualización y reporte"),
]


def add_box(ax, x, y, width, height, label, *, fill, edge, dashed=False, text_color=TEXT,
            font_size=10, line_width=2.0):
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.04,rounding_size=0.10",
        linewidth=line_width,
        linestyle=(0, (5, 3)) if dashed else "solid",
        edgecolor=edge,
        facecolor=fill,
        zorder=3,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2, y + height / 2, label,
        ha="center", va="center", color=text_color,
        fontsize=font_size, linespacing=1.45, zorder=4,
    )
    return box


def add_arrow(ax, start, end, *, connectionstyle="arc3,rad=0"):
    arrow = FancyArrowPatch(
        start, end,
        arrowstyle="Simple,tail_width=0.6,head_width=6,head_length=8",
        color=ORANGE,
        linewidth=0,
        connectionstyle=connectionstyle,
        mutation_scale=1,
        zorder=2,
    )
    ax.add_patch(arrow)


def draw_stage(ax, stage):
    if stage["versioned"]:
        fill, edge, text_color, dashed = NAVY, NAVY, WHITE, False
    else:
        fill, edge, text_color, dashed = WHITE, NAVY, NAVY, True
    label = (
        f"{stage['name']}\n\n{stage['tools']}\n\n"
        f"{stage['machine']}\nEstado: {stage['status']}"
    )
    add_box(
        ax, stage["x"], stage["y"], stage["width"], stage["height"], label,
        fill=fill, edge=edge, dashed=dashed, text_color=text_color, font_size=8.9,
    )


def render(output_path):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(0.55, 8.32, "Arquitectura del flujo de datos", color=NAVY,
            fontsize=25, fontweight="bold", ha="left", va="center")

    for left, right, title, subtitle in LANES:
        ax.text((left + right) / 2, 7.55, title, color=NAVY, fontsize=11,
                fontweight="bold", ha="center", va="center")
        ax.text((left + right) / 2, 7.20, subtitle, color=TEXT_MUTED, fontsize=8.5,
                ha="center", va="center")
        ax.plot([left, right], [6.85, 6.85], color=GRID, linewidth=1.5, zorder=1)

    for x in (4.05, 8.95, 12.95):
        ax.plot([x, x], [1.25, 7.80], color=GRID, linewidth=1.5, zorder=1)

    for stage in STAGES:
        draw_stage(ax, stage)

    add_box(
        ax, HANDOFF["x"], HANDOFF["y"], HANDOFF["width"], HANDOFF["height"],
        HANDOFF["label"], fill=WHITE, edge=ORANGE, text_color=TEXT,
        font_size=7.7, line_width=1.8,
    )
    add_box(
        ax, REPOSITORY["x"], REPOSITORY["y"], REPOSITORY["width"], REPOSITORY["height"],
        REPOSITORY["label"], fill=WHITE, edge=NAVY, text_color=NAVY,
        font_size=8.5, line_width=2.0,
    )

    rstudio, analysis, reporting = STAGES
    mid_y = rstudio["y"] + rstudio["height"] / 2
    add_arrow(ax, (rstudio["x"] + rstudio["width"], mid_y), (HANDOFF["x"], mid_y))
    add_arrow(ax, (HANDOFF["x"] + HANDOFF["width"], mid_y), (analysis["x"], mid_y))
    add_arrow(ax, (analysis["x"] + analysis["width"], mid_y), (reporting["x"], mid_y))
    add_arrow(
        ax,
        (analysis["x"] + analysis["width"] - 0.35, analysis["y"]),
        (REPOSITORY["x"], REPOSITORY["y"] + 0.36),
        connectionstyle="angle3,angleA=-90,angleB=180",
    )
    add_arrow(
        ax,
        (reporting["x"] + reporting["width"], reporting["y"] + 1.15),
        (REPOSITORY["x"], REPOSITORY["y"] + 1.50),
    )

    legend_y = 1.05
    ax.plot([0.78, 1.42], [legend_y, legend_y], color=NAVY, linewidth=2.2)
    ax.text(1.55, legend_y, "Borde sólido: versionado en el repositorio", color=TEXT,
            fontsize=8.6, ha="left", va="center")
    ax.plot([5.38, 6.02], [legend_y, legend_y], color=NAVY, linewidth=2.2,
            linestyle=(0, (5, 3)))
    ax.text(6.15, legend_y, "Borde discontinuo: fuera del repositorio", color=TEXT,
            fontsize=8.6, ha="left", va="center")

    ax.text(
        0.55, 0.46,
        "La etapa de RStudio se documenta para trazabilidad aunque su código vive fuera del repositorio.",
        color=TEXT_MUTED, fontsize=9, ha="left", va="center",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor=WHITE, bbox_inches=None)
    plt.close(fig)
    print(f"Diagrama guardado en: {output_path}")


if __name__ == "__main__":
    render(Path("outputs/arquitectura_flujo.png"))
