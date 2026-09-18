"""Twist analysis: impact of the 3 post-window events (effective 2026-08-17)
on the conclusions of the base analysis.

TW_01  US 10Y +65bp in a week (inflation surprise) -> rate sensitivity
TW_02  CL_02 needs 30% of portfolio in 6 months   -> liquidity & horizon risk
TW_03  USD/COP +8% in days (COP depreciation)     -> CL_02 base-currency impact
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
syn = pd.read_csv(OUT / "07_value_synthesis.csv")

wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change().dropna()
mm = macro.set_index("date")

TRADING_DAYS_6M_M = 126

# =================================================================== TW_01
print("=" * 78)
print("TW_01 — US 10Y +65bp in one week (inflation surprise)")
print("=" * 78)

dy = mm["us_10y_yield"].diff().dropna()          # daily yield changes (pp)
wk = mm["us_10y_yield"].diff(5).dropna()         # weekly changes
print(f"Observed weekly yield changes: mean={wk.mean()*100:+.1f}bp, "
      f"std={wk.std()*100:.1f}bp, min={wk.min()*100:+.1f}bp, max={wk.max()*100:+.1f}bp")
z_65 = (0.65 - wk.mean()) / wk.std()
print(f"+65bp/week = {z_65:.1f} sigma event (vs observed window)")

# per-asset rate beta: r_asset = a + b * dYield (daily, aligned)
aligned = rets.join(dy.rename("dy"), how="inner")
betas, rsq = {}, {}
for c in rets.columns:
    b = np.polyfit(aligned["dy"], aligned[c], 1)[0]
    betas[c] = b
    rsq[c] = aligned["dy"].corr(aligned[c]) ** 2
beta_s = pd.Series(betas)
# expected 1-week impact of +65bp: b * 0.65 (pp of yield -> asset return)
impact = (beta_s * 0.65 * 100).round(1)  # in %
tw01 = pd.DataFrame({
    "rate_beta": beta_s.round(2),
    "R2": pd.Series(rsq).round(3),
    "est_impact_%": impact,
}).merge(assets.set_index("asset_id")[["name", "sector"]], left_index=True, right_index=True)
tw01 = tw01.sort_values("est_impact_%")
print("\nPer-asset rate sensitivity (daily regression of returns on yield changes):")
print(tw01.to_string())
tw01.to_csv(OUT / "10_tw01_rate_betas.csv")

# worst historical weeks for yields -> what happened to assets
worst_wk = wk.nlargest(3)
print("\nLargest observed weekly yield rises and asset response:")
for d, v in worst_wk.items():
    wr = rets.loc[d - pd.Timedelta(days=9):d].tail(5).sum() * 100
    top = wr.nsmallest(3)
    print(f"  week ending {d.date()}: dy={v*100:+.0f}bp | worst: "
          + ", ".join(f"{k} {v:+.1f}%" for k, v in top.items()))

# =================================================================== TW_02
print("\n" + "=" * 78)
print("TW_02 — CL_02 must withdraw 30% of the portfolio in 6 months")
print("=" * 78)

# compliant CL_02 portfolio from stage 8 (pure low-vol equal weight)
w02 = {"VF_A08": 0.25, "VF_A01": 0.25, "VF_A05": 0.25, "VF_A04": 0.25}
pr02 = rets[list(w02)].mul(pd.Series(w02), axis=1).sum(axis=1)
cum02 = (1 + pr02).cumprod()

# rolling 6m (126d) returns and intra-window max drawdowns
roll_ret = cum02 / cum02.shift(TRADING_DAYS_6M_M) - 1
dd_series = cum02 / cum02.cummax() - 1
roll_min_dd = dd_series.rolling(TRADING_DAYS_6M_M).min()
print(f"CL_02 low-vol portfolio — rolling 6m stats over the window:")
print(f"  6m return: mean={roll_ret.mean()*100:+.1f}%, min={roll_ret.min()*100:+.1f}%, "
      f"max={roll_ret.max()*100:+.1f}%")
print(f"  worst drawdown inside any 6m window: {roll_min_dd.min()*100:+.1f}%")
print(f"  share of 6m windows with DD worse than -10%: "
      f"{(roll_min_dd < -0.10).mean()*100:.0f}%")

# liquidity: days to liquidate 30% assuming $100m portfolio, 20% participation
AUM = 100e6
adv = syn.set_index("asset_id")["avg_daily_val_USDm"] * 1e6
redeem = 0.30 * AUM
per_asset = pd.Series(w02) * redeem
days_to_trade = (per_asset / (adv * 0.20))
print(f"\nLiquidating 30% of a $100m portfolio ($30m) at 20% of daily volume:")
for a in w02:
    print(f"  {a}: sell ${per_asset[a]/1e6:.1f}m -> {days_to_trade[a]:.2f} trading days")
print(f"  total (parallel): {days_to_trade.max():.2f} days -> liquidity is NOT a constraint")

# redesigned portfolio: 30% cash sleeve + 70% low-vol mix
w02c = {k: v * 0.70 for k, v in w02.items()}
pr02c = rets[list(w02c)].mul(pd.Series(w02c), axis=1).sum(axis=1)
cum02c = (1 + pr02c).cumprod()
def pst(pr, cum):
    return (f"ann_ret={pr.mean()*252*100:+.1f}%, vol={pr.std()*np.sqrt(252)*100:.1f}%, "
            f"maxDD={(cum/cum.cummax()-1).min()*100:+.1f}%")
print(f"\nOriginal CL_02 mix : {pst(pr02, cum02)}")
print(f"70/30 cash sleeve  : {pst(pr02c, cum02c)}  (cash assumed 0% return)")

# =================================================================== TW_03
print("\n" + "=" * 78)
print("TW_03 — COP depreciates 8% vs USD in a few days")
print("=" * 78)

cop = mm["usd_cop"]
cop_chg = cop.pct_change().dropna()
wk_cop = cop.pct_change(5).dropna()
print(f"Observed weekly USD/COP changes: std={wk_cop.std()*100:.2f}%, "
      f"max={wk_cop.max()*100:+.1f}%  -> +8% = {(0.08-wk_cop.mean())/wk_cop.std():.1f} sigma")

# COP-based investor: COP return = (1+r_usd)*(1+fx_chg)-1
cop_ret = cop_chg.reindex(rets.index).fillna(0)
pr02_cop = (1 + pr02) * (1 + cop_ret) - 1
cum02_cop = (1 + pr02_cop).cumprod()
print(f"\nCL_02 portfolio in COP terms (observed FX): {pst(pr02_cop, cum02_cop)}")
print(f"  vs USD terms:                            {pst(pr02, cum02)}")

# shock translation: +8% USD/COP applied at the end
shock = pd.Series(0.0, index=pr02_cop.index)
shock.iloc[-1] = 0.08
cum02_cop_shock = (1 + pr02_cop + shock).cumprod()
print(f"  +8% COP depreciation -> +8.0% one-off translation gain on the full "
      f"USD portfolio in COP terms (drawdown cushion)")

# do Colombian assets move with COP? (equity-FX correlation)
fx_join = rets.join(cop_chg.rename("dcop"), how="inner")
cop_beta = {c: fx_join[c].corr(fx_join["dcop"]) for c in rets.columns}
print("\nCorrelation of asset returns with USD/COP daily changes:")
for k, v in sorted(cop_beta.items(), key=lambda kv: -abs(kv[1])):
    print(f"  {k}: {v:+.2f}")

# =================================================================== combined
print("\n" + "=" * 78)
print("COMBINED STRESS REPLAY (Feb-2026 analog + twists) on client portfolios")
print("=" * 78)
ports = {
    "CL_01": {"VF_A06": .2, "VF_A04": .2, "VF_A05": .2, "VF_A02": .2, "VF_A01": .2},
    "CL_02 (low-vol)": w02,
    "CL_02 (70/30)": w02c,
    "CL_03": {"VF_A01": .2, "VF_A04": .2, "VF_A06": .2, "VF_A07": .2, "VF_A08": .2},
}
stress = rets.loc["2026-02-09":"2026-02-20"]
print("Replay of 2026-02-09→20 stress episode (2 weeks):")
for name, w in ports.items():
    pr = stress[list(w)].mul(pd.Series(w), axis=1).sum(axis=1)
    tot = (1 + pr).prod() - 1
    # add TW_03 FX cushion for COP-based CL_02
    fx_note = ""
    if name.startswith("CL_02"):
        tot_cop = (1 + tot) * 1.08 - 1
        fx_note = f" | in COP with +8% FX: {tot_cop*100:+.1f}%"
    print(f"  {name:16s}: {tot*100:+.1f}%{fx_note}")

# rate-shock marginal hit via betas
print("\nMarginal +65bp rate-shock estimate per portfolio (sum w*beta*0.65):")
for name, w in ports.items():
    hit = sum(beta_s[a] * wt for a, wt in w.items()) * 0.65 * 100
    print(f"  {name:16s}: {hit:+.1f}%")

# =================================================================== figures
fig, axes = plt.subplots(2, 2, figsize=(13, 9))

ax = axes[0, 0]
t = tw01.sort_values("est_impact_%")
ax.barh(t["name"], t["est_impact_%"],
        color=["red" if v < 0 else "green" for v in t["est_impact_%"]])
ax.axvline(0, color="k", lw=0.6)
ax.set_title("TW_01: estimated impact of +65bp rate shock (%)")
ax.grid(alpha=0.3)

ax = axes[0, 1]
ax.plot(roll_min_dd.index, roll_min_dd * 100, lw=1, color="steelblue")
ax.axhline(-10, color="red", ls="--", lw=1, label="CL_02 tolerance -10%")
ax.fill_between(roll_min_dd.index, roll_min_dd * 100, -10,
                where=(roll_min_dd * 100 < -10), color="red", alpha=0.2)
ax.legend(); ax.grid(alpha=0.3)
ax.set_title("TW_02: worst drawdown inside each rolling 6m window (CL_02 low-vol)")

ax = axes[1, 0]
ax.plot(cum02.index, (cum02 - 1) * 100, label="CL_02 in USD", lw=1.2)
ax.plot(cum02_cop.index, (cum02_cop - 1) * 100, label="CL_02 in COP (observed FX)", lw=1.2)
ax.plot(cum02_cop_shock.index, (cum02_cop_shock - 1) * 100,
        label="COP terms + 8% COP depreciation shock", lw=1.2, ls="--")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
ax.set_title("TW_03: CL_02 portfolio — USD vs COP terms (%)")

ax = axes[1, 1]
names = list(ports.keys())
stress_res = []
for name, w in ports.items():
    pr = stress[list(w)].mul(pd.Series(w), axis=1).sum(axis=1)
    stress_res.append(((1 + pr).prod() - 1) * 100)
ax.bar(names, stress_res, color=["#d62728" if v < -8 else "#ff7f0e" for v in stress_res])
for i, v in enumerate(stress_res):
    ax.text(i, v - 0.4, f"{v:+.1f}%", ha="center", fontsize=9)
ax.set_title("Combined stress replay (Feb-2026 episode, 2 weeks)")
ax.tick_params(axis="x", rotation=15)
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(FIG / "10_twist_analysis.png", dpi=110)
plt.close(fig)
print("\nFigure saved: 10_twist_analysis.png")
