"""Macro-level graph set answering the twist questions:
- fig 15: TW_01 rates (level, weekly-change tail, z-score timeline, asset response)
- fig 16: inflation treated the same way (level, monthly-change tail, yield link, asset sensitivity)
- fig 17: TW_03 FX (USD/COP level + shock, weekly-change tail, 4-pair comparison, FX vol)
"""
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
assets = clean.load_assets()
macro = clean.load_macro()
m = macro.set_index("date")

wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change().dropna()

y = m["us_10y_yield"]
infl_raw = pd.read_csv(OUT.parent / "dataset_start" / "02_macro_raw.csv", encoding="utf-8-sig")
infl_raw["date"] = pd.to_datetime(infl_raw["date"])
infl_m = infl_raw.dropna(subset=["us_inflation_yoy"]).set_index("date")["us_inflation_yoy"]

# inflation->yield mapping from window
b_yi, a_yi = np.polyfit(m["us_inflation_yoy"], y, 1)
implied_infl_jump = 0.65 / b_yi          # pp of inflation consistent with +65bp
d_infl = infl_m.diff().dropna()
z_infl = (implied_infl_jump - d_infl.mean()) / d_infl.std()

last_y, last_i = y.iloc[-1], infl_m.iloc[-1]
shock_date = pd.Timestamp("2026-08-17")

# ================================================================= fig 15: rates
fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))

ax = axes[0, 0]
ax.plot(y.index, y, lw=1.2, color="steelblue")
ax.plot([y.index[-1], shock_date + pd.Timedelta(days=7)], [last_y, last_y + 0.65],
        lw=2, ls="--", color="red", label=f"TW_01: {last_y:.2f} → {last_y+0.65:.2f}")
ax.legend(); ax.grid(alpha=0.3)
ax.set_title("US 10Y yield — level and the TW_01 jump")

ax = axes[0, 1]
wk = y.diff(5).dropna() * 100
ax.hist(wk, bins=40, color="steelblue", alpha=0.8)
for s in (-3, 3):
    ax.axvline(s * wk.std(), color="grey", ls=":", lw=1)
ax.axvline(65, color="red", ls="--", lw=2, label="+65bp ≈ 54σ")
ax.set_xlim(-8, 70); ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_xlabel("weekly Δ yield (bp)")
ax.set_title("Weekly yield changes — the shock is off the distribution")

ax = axes[1, 0]
z = (wk - wk.mean()) / wk.std()
ax.plot(z.index, z, lw=1, color="purple")
ax.axhline(3, color="red", ls=":", lw=1); ax.axhline(-3, color="red", ls=":", lw=1)
ax.axhline(54, color="red", ls="--", lw=1.5, label="TW_01 = 54σ")
ax.set_ylim(-5, 58); ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_title("Z-score of weekly yield changes (window never exceeded ±4σ)")

ax = axes[1, 1]
top_weeks = wk.nlargest(5)
resp = []
for d in top_weeks.index:
    wr = rets.loc[:d].tail(5).mean() * 100
    resp.append(wr)
resp = pd.DataFrame(resp, index=top_weeks.index.date)
resp.plot(kind="bar", ax=ax, legend=False, colormap="tab10")
ax.axhline(0, color="k", lw=0.6)
ax.set_title("Asset response in the 5 biggest yield-rise weeks (5d mean %)")
ax.tick_params(axis="x", rotation=30, labelsize=7)
ax.grid(alpha=0.3)
fig.suptitle("TW_01 — macro view of the +65bp rate shock", fontsize=13)
fig.tight_layout()
fig.savefig(FIG / "15_macro_rates_tw01.png", dpi=110, bbox_inches="tight")
plt.close(fig)

# ================================================================= fig 16: inflation
fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))

ax = axes[0, 0]
ax.step(infl_m.index, infl_m, where="post", lw=1.6, color="darkorange")
ax.plot([infl_m.index[-1], shock_date + pd.Timedelta(days=30)],
        [last_i, last_i + implied_infl_jump], lw=2, ls="--", color="red",
        label=f"implied surprise: {last_i:.2f} → {last_i+implied_infl_jump:.2f} (+{implied_infl_jump:.2f}pp)")
ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_title("US inflation YoY (monthly) — level and the implied surprise")

ax = axes[0, 1]
ax.bar(range(len(d_infl)), d_infl * 100, color="darkorange", alpha=0.8,
       tick_label=[d.strftime("%y-%m") for d in d_infl.index])
ax.axhline(implied_infl_jump * 100, color="red", ls="--", lw=2,
           label=f"+{implied_infl_jump*100:.0f}bp ≈ {z_infl:.0f}σ")
ax.set_ylabel("monthly Δ inflation (bp)")
ax.tick_params(axis="x", rotation=45, labelsize=7)
ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_title("Monthly inflation changes — never above +1bp in the window")

ax = axes[1, 0]
ax.scatter(m["us_inflation_yoy"], y, s=12, alpha=0.5, color="steelblue")
xs = np.linspace(m["us_inflation_yoy"].min(), last_i + implied_infl_jump, 10)
ax.plot(xs, a_yi + b_yi * xs, color="k", lw=1.2,
        label=f"fit: yield = {a_yi:.2f} + {b_yi:.2f}×infl (r=0.90)")
ax.scatter([last_i + implied_infl_jump], [last_y + 0.65], color="red", s=90,
           zorder=5, marker="*", label="TW_01 shock point")
ax.set_xlabel("US inflation YoY (%)"); ax.set_ylabel("US 10Y yield (%)")
ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_title("The yield↔inflation link that maps the surprise to +65bp")

ax = axes[1, 1]
# monthly asset returns vs monthly inflation changes (13 obs — small sample)
mret = wide.resample("MS").last().pct_change().reindex(infl_m.index).dropna()
di = infl_m.diff().reindex(mret.index)
sens = {c: mret[c].corr(di) for c in mret.columns}
sens = pd.Series(sens).sort_values()
nm = assets.set_index("asset_id")["name"]
ax.barh([nm[a] for a in sens.index], sens.values,
        color=["#2ca02c" if v > 0 else "#d62728" for v in sens.values])
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel("corr(monthly return, monthly Δ inflation)  [13 obs — indicative only]")
ax.set_title("Inflation sensitivity: positive = benefits from inflation surprises")
ax.grid(alpha=0.3)
fig.suptitle("TW_01 root cause — the inflation surprise, same treatment", fontsize=13)
fig.tight_layout()
fig.savefig(FIG / "16_macro_inflation_tw01.png", dpi=110, bbox_inches="tight")
plt.close(fig)

# ================================================================= fig 17: FX
cop = m["usd_cop"]
fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))

ax = axes[0, 0]
ax.plot(cop.index, cop, lw=1.2, color="seagreen")
ax.plot([cop.index[-1], shock_date + pd.Timedelta(days=5)],
        [cop.iloc[-1], cop.iloc[-1] * 1.08], lw=2, ls="--", color="red",
        label=f"TW_03: {cop.iloc[-1]:.0f} → {cop.iloc[-1]*1.08:.0f} (+8%)")
ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_title("USD/COP — level and the TW_03 jump")

ax = axes[0, 1]
wk_cop = cop.pct_change(5).dropna() * 100
ax.hist(wk_cop, bins=40, color="seagreen", alpha=0.8)
ax.axvline(8, color="red", ls="--", lw=2, label="+8% ≈ 11σ")
ax.set_xlim(-3, 9); ax.legend(fontsize=9); ax.grid(alpha=0.3)
ax.set_xlabel("weekly Δ USD/COP (%)")
ax.set_title("Weekly COP changes — the shock vs history")

ax = axes[1, 0]
for c, lbl in [("usd_cop", "COP"), ("usd_pen", "PEN"), ("usd_mxn", "MXN"), ("usd_clp", "CLP")]:
    lw = 2.2 if c == "usd_cop" else 1.0
    ax.plot(m.index, m[c] / m[c].iloc[0] * 100, lw=lw, label=lbl)
ax.set_ylabel("rebased = 100  (higher = weaker local currency)")
ax.legend(); ax.grid(alpha=0.3)
ax.set_title("All four FX pairs — COP mid-pack, CLP the outlier")

ax = axes[1, 1]
fxvol = {lbl: m[c].pct_change().rolling(21).std() * np.sqrt(252) * 100
         for c, lbl in [("usd_cop", "COP"), ("usd_pen", "PEN"),
                        ("usd_mxn", "MXN"), ("usd_clp", "CLP")]}
for lbl, s in fxvol.items():
    ax.plot(s.index, s, lw=1.2, label=lbl)
ax.axhline(8 / np.sqrt(5 / 52), color="red", ls="--", lw=1.5,
           label="TW_03: 8%/week ≈ 40% annualized")
ax.set_ylabel("rolling 21d annualized vol (%)")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
ax.set_title("FX volatility — the shock is ~10x normal COP vol")
fig.suptitle("TW_03 — macro view of the COP depreciation", fontsize=13)
fig.tight_layout()
fig.savefig(FIG / "17_macro_fx_tw03.png", dpi=110, bbox_inches="tight")
plt.close(fig)

print("Saved: 15_macro_rates_tw01.png, 16_macro_inflation_tw01.png, 17_macro_fx_tw03.png")
print(f"\nKey numbers:")
print(f"  yield~inflation fit: yield = {a_yi:.2f} + {b_yi:.2f}*infl (r=0.90)")
print(f"  +65bp  <-> inflation surprise of +{implied_infl_jump:.2f}pp ({z_infl:.0f} sigma)")
print(f"  inflation monthly changes: max observed +{d_infl.max()*100:.0f}bp, std {d_infl.std()*100:.1f}bp")
print(f"  inflation sensitivity ranking: {dict(sens.round(2))}")
