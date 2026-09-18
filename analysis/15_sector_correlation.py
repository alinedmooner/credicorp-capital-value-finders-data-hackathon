"""Render a presentation-ready sector correlation matrix."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

import clean
from chart_style import GRID, NAVY, ORANGE, TEXT, WHITE, add_note, configure


OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
PRESENTATION = OUT.parent / "outputs"
SECTOR_LABELS = {
    "Consumer Staples": "Consumo básico",
    "Technology": "Tecnología",
    "Energy": "Energía",
    "Financials": "Financiero",
    "Health Care": "Salud",
    "Industrials": "Industrial",
    "Materials": "Materiales",
    "Utilities": "Servicios públicos",
}


def render():
    configure()
    prices = clean.load_prices_daily()
    assets = clean.load_assets().set_index("asset_id")
    closes = prices.pivot_table(index="date", columns="asset_id", values="close")
    correlations = closes.pct_change().corr()
    sectors = [SECTOR_LABELS[assets.loc[asset, "sector"]] for asset in correlations.columns]
    display = correlations.to_numpy(copy=True)
    np.fill_diagonal(display, np.nan)

    cmap = LinearSegmentedColormap.from_list("matriz", [WHITE, "#F6D7C4", ORANGE])
    cmap.set_bad(NAVY)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.subplots_adjust(left=0.22, right=0.82, top=0.85, bottom=0.15)
    fig.suptitle("Matriz de correlación entre sectores", x=0.08, ha="left", color=NAVY,
                 fontsize=22, fontweight="bold")

    image = ax.imshow(display, cmap=cmap, vmin=0, vmax=0.30, aspect="equal")
    ax.set_xticks(range(len(sectors)), sectors, rotation=35, ha="right")
    ax.set_yticks(range(len(sectors)), sectors)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.set_xticks(np.arange(-0.5, len(sectors), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(sectors), 1), minor=True)
    ax.grid(which="minor", color=WHITE, linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row in range(len(sectors)):
        for column in range(len(sectors)):
            if row == column:
                ax.text(column, row, "1,00", ha="center", va="center", color=WHITE,
                        fontsize=10, fontweight="bold")
            else:
                value = correlations.iloc[row, column]
                text_color = NAVY if value >= 0.20 else TEXT
                ax.text(column, row, f"{value:.2f}".replace(".", ","), ha="center",
                        va="center", color=text_color, fontsize=10)

    colorbar = fig.colorbar(image, ax=ax, fraction=0.048, pad=0.04)
    colorbar.set_label("Correlación diaria", color=TEXT)
    colorbar.set_ticks([0, 0.10, 0.20, 0.30])
    colorbar.ax.set_yticklabels(["0,00", "0,10", "0,20", "0,30"])
    ax.set_title("Rendimientos diarios · la diagonal corresponde al mismo sector", loc="left",
                 fontsize=12, pad=16)
    add_note(fig, "Fuente: precios diarios limpios. El universo cuenta con una acción representativa por sector.")

    for path in (FIG / "02_correlations.png", PRESENTATION / "matriz_correlacion_sectores.png"):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=200)
    plt.close(fig)
    print("Gráficas guardadas: 02_correlations.png y matriz_correlacion_sectores.png")


if __name__ == "__main__":
    render()
