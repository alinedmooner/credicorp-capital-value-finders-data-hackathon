"""Stage 5: macro dataset — coverage, regimes, FX moves, correlations with assets."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import clean

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"

m = clean.load_macro()
px = clean.load_prices_daily()
assets = clean.load_assets()

print("=" * 78)
print("MACRO OVERVIEW")
print("=" * 78)
print(f"rows: {len(m)}, range: {m.date.min().date()} -> {m.date.max().date()}")
print("\nDescribe:")
print(m.drop(columns=["date", "risk_regime"]).describe().round(3).to_string())

print("\nRisk regime counts:")
print(m["risk_regime"].value_counts().to_string())
print("\nRegime date ranges:")
for r, g in m.groupby("risk_regime"):
    print(f"  {r}: {g.date.min().date()} -> {g.date.max().date()}  ({len(g)} days)")

print("\nFX change over window:")
for c in ["usd_cop", "usd_pen", "usd_mxn", "usd_clp"]:
    chg = m[c].iloc[-1] / m[c].iloc[0] - 1
    print(f"  {c}: {m[c].iloc[0]:.2f} -> {m[c].iloc[-1]:.2f}  ({chg*100:+.1f}%)")
print(f"  us_10y_yield: {m.us_10y_yield.iloc[0]:.2f} -> {m.us_10y_yield.iloc[-1]:.2f}")
print(f"  inflation (ffilled): {m.us_inflation_yoy.iloc[0]} -> {m.us_inflation_yoy.iloc[-1]}")

# market_factor vs asset returns
wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change()
mm = m.set_index("date")
joined = rets.join(mm[["market_factor", "risk_regime"]], how="inner")

print("\nCorrelation of daily asset returns with market_factor:")
cf = joined[[c for c in joined.columns if c.startswith("VF")]].corrwith(joined["market_factor"]).round(3)
print(cf.to_string())

print("\nAverage daily return by risk regime (bps):")
by_regime = joined.groupby("risk_regime")[[c for c in joined.columns if c.startswith("VF")]].mean() * 1e4
print(by_regime.round(2).to_string())
print("\nDaily vol by risk regime (%):")
vol_regime = joined.groupby("risk_regime")[[c for c in joined.columns if c.startswith("VF")]].std() * 100
print(vol_regime.round(2).to_string())

# macro correlations among themselves
print("\nMacro internal correlations:")
mc = m.drop(columns=["date"]).copy()
mc["risk_regime"] = mc["risk_regime"].astype("category").cat.codes
print(m.drop(columns=["date", "risk_regime"]).corr().round(2).to_string())

# ------------------------------------------------------------------ figures
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
axes[0].plot(m.date, m.us_10y_yield, label="US 10Y yield (%)")
ax2 = axes[0].twinx()
ax2.plot(m.date, m.us_inflation_yoy, color="orange", label="US infl YoY (%)", alpha=0.7)
axes[0].legend(loc="upper left"); ax2.legend(loc="upper right")
axes[0].grid(alpha=0.3); axes[0].set_title("Rates & inflation")
for c in ["usd_cop", "usd_pen", "usd_mxn", "usd_clp"]:
    axes[1].plot(m.date, m[c] / m[c].iloc[0], label=c.upper())
axes[1].legend(ncol=4, fontsize=8); axes[1].grid(alpha=0.3)
axes[1].set_title("FX vs USD (rebased)")
axes[2].plot(m.date, m.market_factor, lw=0.8, color="purple")
# shade regimes
colors = {"Stress": "red", "Recovery": "orange", "Normal": "green"}
for r, g in m.groupby("risk_regime"):
    axes[2].axvspan(g.date.min(), g.date.max(), color=colors[r], alpha=0.12, label=r)
axes[2].legend(); axes[2].grid(alpha=0.3)
axes[2].set_title("Market factor with risk regimes shaded")
fig.tight_layout()
fig.savefig(FIG / "05_macro.png", dpi=110)
plt.close(fig)

print("\nFigure saved: 05_macro.png")
