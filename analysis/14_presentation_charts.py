"""Render presentation-ready macro and event-cut charts."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import clean
from chart_style import (GRID, NAVY, ORANGE, SERIES, TEXT, TEXT_MUTED, add_note,
                         configure, style_axis)


OUT = Path(__file__).resolve().parent
PRESENTATION = OUT.parent / "outputs"
EVENT_CUTS = [
    ("VF_A02", pd.Timestamp("2025-08-21"), "A02 · 21 ago. 2025"),
    ("VF_A02", pd.Timestamp("2026-01-10"), "A02 · 10 ene. 2026"),
    ("VF_A03", pd.Timestamp("2026-04-06"), "A03 · 6 abr. 2026"),
    ("VF_A04", pd.Timestamp("2026-05-18"), "A04 · 18 may. 2026"),
    ("VF_A07", pd.Timestamp("2026-06-08"), "A07 · 8 jun. 2026"),
]


def render_inflation_and_fx():
    configure()
    macro = clean.load_macro().set_index("date")
    raw_macro = pd.read_csv(OUT.parent / "dataset_start" / "02_macro_raw.csv", encoding="utf-8-sig")
    raw_macro["date"] = pd.to_datetime(raw_macro["date"])
    inflation = raw_macro.dropna(subset=["us_inflation_yoy"]).set_index("date")["us_inflation_yoy"]
    fx_columns = [("usd_cop", "COP"), ("usd_pen", "PEN"), ("usd_mxn", "MXN"), ("usd_clp", "CLP")]

    fig, (ax_inflation, ax_fx) = plt.subplots(2, 1, figsize=(16, 9), dpi=200,
                                                gridspec_kw={"height_ratios": [1, 1.25], "hspace": 0.34})
    fig.subplots_adjust(left=0.08, right=0.92, top=0.90, bottom=0.10)
    fig.suptitle("Inflación y tipos de cambio frente al dólar", x=0.08, ha="left",
                 color=NAVY, fontsize=22, fontweight="bold")

    ax_inflation.step(inflation.index, inflation, where="post", color=ORANGE, lw=2.8,
                      label="Inflación anual de EE. UU.")
    ax_inflation.set_ylabel("Inflación anual (%)")
    ax_inflation.set_title("Inflación de EE. UU. y USD/COP", loc="left", fontsize=12, pad=10)
    style_axis(ax_inflation)
    fx_twin = ax_inflation.twinx()
    fx_twin.plot(macro.index, macro["usd_cop"], color=NAVY, lw=1.8, label="USD/COP")
    fx_twin.set_ylabel("Pesos colombianos por USD", color=NAVY)
    fx_twin.tick_params(axis="y", colors=NAVY)
    fx_twin.spines["top"].set_visible(False)
    lines = ax_inflation.get_lines() + fx_twin.get_lines()
    ax_inflation.legend(lines, [line.get_label() for line in lines], loc="upper left")

    for index, (column, label) in enumerate(fx_columns):
        rebased = macro[column] / macro[column].iloc[0] * 100
        ax_fx.plot(rebased.index, rebased, color=SERIES[index], lw=2.1,
                   label=f"USD/{label}")
    ax_fx.axhline(100, color=TEXT_MUTED, lw=1, ls=(0, (2, 3)))
    ax_fx.set_ylabel("Índice base 100")
    ax_fx.set_title("Evolución acumulada de las monedas · un aumento indica debilitamiento frente al USD",
                    loc="left", fontsize=12, pad=10)
    ax_fx.legend(ncol=4, loc="upper left")
    style_axis(ax_fx)
    add_note(fig, "Fuente: serie macroeconómica diaria. La inflación es mensual y se muestra en sus fechas publicadas.")

    path = PRESENTATION / "inflacion_tipo_cambio.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print("Gráfica guardada: inflacion_tipo_cambio.png")


def render_selected_assets_with_cuts():
    configure()
    prices = clean.load_prices_daily()
    wide = prices.pivot_table(index="date", columns="asset_id", values="close")
    selected = ["VF_A02", "VF_A03", "VF_A04", "VF_A07"]
    rebased = wide[selected] / wide[selected].iloc[0] * 100
    colors = {asset: SERIES[index + 1] for index, asset in enumerate(selected)}

    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.subplots_adjust(left=0.08, right=0.94, top=0.88, bottom=0.12)
    fig.suptitle("Acciones seleccionadas y fechas de corte", x=0.08, ha="left",
                 color=NAVY, fontsize=22, fontweight="bold")

    for asset in selected:
        ax.plot(rebased.index, rebased[asset], color=colors[asset], lw=2.2, label=asset, zorder=3)
    ax.axhline(100, color=TEXT_MUTED, lw=1, ls=(0, (2, 3)), zorder=1)

    top = 0.98
    for index, (asset, date, label) in enumerate(EVENT_CUTS):
        ax.axvline(date, color=ORANGE, lw=1.45, ls=(0, (4, 3)), zorder=2)
        ax.annotate(
            label, xy=(date, top - (index % 2) * 0.095), xycoords=("data", "axes fraction"),
            xytext=(4, 0), textcoords="offset points", rotation=90,
            color=TEXT, fontsize=8.5, va="top", ha="left",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": GRID},
        )

    ax.set_ylabel("Índice base 100")
    ax.set_title("Precio de cierre acumulado · cortes solicitados", loc="left", fontsize=12, pad=10)
    ax.legend(ncol=4, loc="lower left")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    style_axis(ax)
    add_note(fig, "Fuente: precios diarios limpios. El corte del 10-ene-2026 se muestra como fecha de calendario, aunque no hubo rueda.")

    path = PRESENTATION / "acciones_cortes.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print("Gráfica guardada: acciones_cortes.png")


if __name__ == "__main__":
    render_inflation_and_fx()
    render_selected_assets_with_cuts()
