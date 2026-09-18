"""Stage 4: intraday (10-min) data — coverage, session structure, consistency vs daily."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import clean

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"

it = clean.load_prices_intraday()
px = clean.load_prices_daily()

print("=" * 78)
print("INTRADAY COVERAGE")
print("=" * 78)
it["d"] = it["date"].dt.date
it["t"] = it["date"].dt.time

cov = it.groupby("asset_id").agg(
    n_rows=("date", "count"),
    n_days=("d", "nunique"),
    first=("date", "min"),
    last=("date", "max"),
)
cov["avg_bars_day"] = (cov.n_rows / cov.n_days).round(1)
print(cov.to_string())

print("\nBars per day distribution (all assets):")
bpd = it.groupby(["asset_id", "d"]).size()
print(bpd.value_counts().head(10).to_string())

print("\nSession times:")
print("min time:", it["t"].min(), "| max time:", it["t"].max())
print("unique bar times:", it["t"].nunique())

print("\nYearly row counts:")
print(it.groupby(it.date.dt.year).size().to_string())

# ---------------------------------------------------------- consistency vs daily
print("\n" + "=" * 78)
print("CONSISTENCY: intraday-aggregated daily close vs daily file (overlap period)")
print("=" * 78)
agg = it.groupby(["asset_id", "d"]).agg(
    intra_open=("open", "first"),
    intra_close=("close", "last"),
    intra_high=("high", "max"),
    intra_low=("low", "min"),
    intra_vol=("volume", "sum"),
).reset_index()
agg["date"] = pd.to_datetime(agg["d"])
cmp = px.merge(agg, on=["asset_id", "date"], how="inner")
cmp["close_diff_%"] = (cmp["close"] / cmp["intra_close"] - 1) * 100
cmp["vol_ratio"] = cmp["volume"] / cmp["intra_vol"]

summ = cmp.groupby("asset_id").agg(
    overlap_days=("date", "count"),
    med_close_diff_pct=("close_diff_%", "median"),
    max_abs_close_diff_pct=("close_diff_%", lambda s: s.abs().max()),
    med_vol_ratio=("vol_ratio", "median"),
).round(2)
print(summ.to_string())

print("\nLargest close discrepancies (top 10):")
worst = cmp.reindex(cmp["close_diff_%"].abs().sort_values(ascending=False).index)
print(worst[["date", "asset_id", "close", "intra_close", "close_diff_%"]].head(10).to_string(index=False))

# ratio over time for one asset to check for level shifts
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
for aid in ["VF_A01", "VF_A06"]:
    c = cmp[cmp.asset_id == aid].sort_values("date")
    axes[0].plot(c["date"], c["close"], lw=1, label=f"{aid} daily file")
    axes[0].plot(c["date"], c["intra_close"], lw=1, ls="--", label=f"{aid} intraday agg")
axes[0].legend(); axes[0].grid(alpha=0.3); axes[0].set_title("Daily file vs intraday-aggregated close")
for aid in ["VF_A01", "VF_A02", "VF_A03", "VF_A04", "VF_A05", "VF_A06", "VF_A07", "VF_A08"]:
    c = cmp[cmp.asset_id == aid].sort_values("date")
    axes[1].plot(c["date"], c["close"] / c["intra_close"], lw=0.8, label=aid)
axes[1].legend(ncol=4, fontsize=7); axes[1].grid(alpha=0.3)
axes[1].set_title("Ratio daily/intraday close (1.0 = consistent)")
fig.tight_layout()
fig.savefig(FIG / "04_intraday_vs_daily.png", dpi=110)
plt.close(fig)

# intraday seasonality: average volume by bar time
vol_t = it.groupby("t")["volume"].mean()
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot([str(x) for x in vol_t.index], vol_t.values)
ax.set_title("Average intraday volume by bar time (U-shape check)")
ax.set_xticks(range(0, len(vol_t), 4))
ax.tick_params(axis="x", rotation=45, labelsize=7)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "04_intraday_volume_curve.png", dpi=110)
plt.close(fig)

print("\nFigures saved: 04_intraday_vs_daily.png, 04_intraday_volume_curve.png")
