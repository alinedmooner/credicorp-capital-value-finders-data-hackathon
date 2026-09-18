"""Cumulative performance with linear trend lines and variance visualization."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import clean

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"

px = clean.load_prices_daily()
wide = px.pivot_table(index="date", columns="asset_id", values="close")
cum = wide / wide.iloc[0]
rets = wide.pct_change()

x = np.arange(len(cum))  # trading-day index for regression

fig, (ax, axv) = plt.subplots(
    2, 1, figsize=(13, 8.5), sharex=True,
    gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.08})

colors = plt.cm.tab10.colors
for i, c in enumerate(cum.columns):
    y = cum[c].values
    # linear trend on rebased cumulative
    slope, intercept = np.polyfit(x, y, 1)
    trend = slope * x + intercept
    ann_vol = rets[c].std() * np.sqrt(252) * 100
    slope_bp_day = slope * 100  # rebased units per day -> %
    ax.plot(cum.index, y, lw=1.1, color=colors[i], alpha=0.85,
            label=f"{c}  σ={ann_vol:.0f}%  trend={slope_bp_day:+.2f}%/d")
    ax.plot(cum.index, trend, lw=1.6, ls="--", color=colors[i], alpha=0.9)
    # end-of-line trend annotation
    ax.annotate(f"{trend[-1]:.2f}", (cum.index[-1], trend[-1]),
                textcoords="offset points", xytext=(5, 0), fontsize=7,
                color=colors[i])
    # rolling 21d annualized volatility (variance behavior)
    roll_vol = rets[c].rolling(21).std() * np.sqrt(252) * 100
    axv.plot(cum.index, roll_vol, lw=1.0, color=colors[i], alpha=0.85)

ax.axhline(1.0, color="k", lw=0.6, alpha=0.5)
ax.set_title("Cumulative performance (rebased) with linear trend (dashed) — "
             "legend shows annualized volatility σ and trend slope")
ax.legend(ncol=2, fontsize=8, loc="upper left")
ax.grid(alpha=0.3)
ax.margins(x=0.03)

axv.set_ylabel("Roll. 21d vol (%)", fontsize=8)
axv.set_xlabel("Date")
axv.grid(alpha=0.3)
axv.set_title("Variance behavior: 21-day rolling annualized volatility", fontsize=9)

fig.tight_layout()
out = FIG / "09_cumulative_trend_variance.png"
fig.savefig(out, dpi=110, bbox_inches="tight")
plt.close(fig)
print(f"Saved -> {out}")

# print trend + variance summary table
print("\nasset  ann_vol_%  trend_%/day  trend_total_(end value)")
for i, c in enumerate(cum.columns):
    y = cum[c].values
    slope, intercept = np.polyfit(x, y, 1)
    print(f"{c}  {rets[c].std()*np.sqrt(252)*100:6.1f}  {slope*100:+8.3f}  {(slope*x[-1]+intercept):8.2f}")
