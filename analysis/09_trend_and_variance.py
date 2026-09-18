"""Render cumulative performance and rolling-volatility presentation chart."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import clean
from chart_style import NAVY, SERIES, TEXT_MUTED, add_note, configure, style_axis


OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
PRESENTATION = OUT.parent / "outputs"


def render():
    configure()
    prices = clean.load_prices_daily()
    wide = prices.pivot_table(index="date", columns="asset_id", values="close")
    cumulative = wide / wide.iloc[0] * 100
    returns = wide.pct_change()
    x = np.arange(len(cumulative))

    fig, (ax_return, ax_volatility) = plt.subplots(
        2, 1, figsize=(16, 9), dpi=200, sharex=True,
        gridspec_kw={"height_ratios": [3.1, 1.35], "hspace": 0.12},
    )
    fig.subplots_adjust(left=0.08, right=0.88, top=0.90, bottom=0.10)
    fig.suptitle("Rendimiento acumulado y volatilidad móvil", x=0.08, ha="left",
                 color=NAVY, fontsize=22, fontweight="bold")

    for index, asset in enumerate(cumulative.columns):
        color = SERIES[index]
        values = cumulative[asset].values
        slope, intercept = np.polyfit(x, values, 1)
        trend = slope * x + intercept
        annual_volatility = returns[asset].std() * np.sqrt(252) * 100
        ax_return.plot(cumulative.index, values, color=color, lw=1.8, label=asset, zorder=3)
        ax_return.plot(cumulative.index, trend, color=color, lw=1.2, ls=(0, (4, 3)), alpha=0.72)
        ax_return.annotate(
            f"{asset}  {values[-1] - 100:+.0f}%",
            (cumulative.index[-1], values[-1]), xytext=(7, 0),
            textcoords="offset points", color=color, fontsize=8, va="center",
            clip_on=False,
        )
        rolling_volatility = returns[asset].rolling(21).std() * np.sqrt(252) * 100
        ax_volatility.plot(rolling_volatility.index, rolling_volatility, color=color,
                           lw=1.55, label=f"{asset} · {annual_volatility:.0f}%")

    ax_return.axhline(100, color=TEXT_MUTED, lw=1, ls=(0, (2, 3)), zorder=1)
    ax_return.set_ylabel("Índice base 100")
    ax_return.set_title("Precio de cierre acumulado · línea discontinua: tendencia lineal",
                        loc="left", fontsize=12, pad=10)
    style_axis(ax_return)
    ax_return.legend(ncol=4, loc="upper left", fontsize=9, title="Acciones")

    ax_volatility.set_ylabel("Volatilidad anualizada (%)")
    ax_volatility.set_title("Volatilidad móvil de 21 ruedas", loc="left", fontsize=12, pad=10)
    ax_volatility.legend(ncol=4, loc="upper left", fontsize=8,
                          title="Volatilidad del período")
    style_axis(ax_volatility)

    add_note(fig, "Fuente: precios diarios limpios. Las etiquetas finales muestran el rendimiento acumulado.")
    for path in (FIG / "09_cumulative_trend_variance.png", PRESENTATION / "rendimiento_volatilidad.png"):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=200)
    plt.close(fig)
    print("Gráficas guardadas: 09_cumulative_trend_variance.png y rendimiento_volatilidad.png")


if __name__ == "__main__":
    render()
