"""Twist-focused graph set: one figure per twist + combined summary dashboard."""
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

w02 = {"VF_A08": 0.25, "VF_A01": 0.25, "VF_A05": 0.25, "VF_A04": 0.25}
w02c = {k: v * 0.70 for k, v in w02.items()}
pr02 = rets[list(w02)].mul(pd.Series(w02), axis=1).sum(axis=1)
pr02c = rets[list(w02c)].mul(pd.Series(w02c), axis=1).sum(axis=1)
cum02, cum02c = (1 + pr02).cumprod(), (1 + pr02c).cumprod()

# ------------------------------------------------------------------ fig 1: TW_01
wk = mm["us_10y_yield"].diff(5).dropna() * 100  # bp
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
ax.hist(wk, bins=40, color="steelblue", alpha=0.8, label="observed weekly Δ yield")
ax.axvline(65, color="red", lw=2, ls="--", label="TW_01 shock: +65bp (≈54σ)")
ax.set_xlabel("Weekly change in US 10Y yield (bp)")
ax.set_title("TW_01 — the shock lives far outside observed history")
ax.legend(); ax.grid(alpha=0.3)
ax.set_xlim(-10, 70)

ax = axes[1]
lev = syn.set_index("asset_id")["nd_ebitda"]
nm = assets.set_index("asset_id")["name"]
order = lev.sort_values(ascending=False)
colors = ["#d62728" if v == order.max() else "#1f77b4" for v in order]
ax.barh([nm[a] for a in order.index], order.values, color=colors)
ax.axvline(0, color="k", lw=0.6)
ax.set_xlabel("Net debt / EBITDA (LTM)")
ax.set_title("TW_01 transmission channel: leverage (red = most exposed)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "11_tw01_rate_shock.png", dpi=110, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ fig 2: TW_02
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
roll_ret = (cum02 / cum02.shift(126) - 1).dropna() * 100
ax.hist(roll_ret, bins=30, color="seagreen", alpha=0.8)
ax.axvline(0, color="k", lw=0.8)
ax.axvline(roll_ret.min(), color="red", ls="--", lw=1.5,
           label=f"worst 6m: {roll_ret.min():+.1f}%")
ax.set_xlabel("Rolling 6-month return (%)")
ax.set_title("TW_02 — CL_02 low-vol mix: every 6m window ended near/above zero")
ax.legend(); ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(cum02.index, (cum02 - 1) * 100, lw=1.3, label="current low-vol mix (maxDD −9.3%)")
ax.plot(cum02c.index, (cum02c - 1) * 100, lw=1.3,
        label="70/30 cash sleeve (maxDD −6.6%)")
# drawdown shading for current mix
dd = (cum02 / cum02.cummax() - 1) * 100
ax2 = ax.twinx()
ax2.fill_between(dd.index, dd, 0, color="steelblue", alpha=0.15)
ax2.set_ylabel("Drawdown (%)", color="steelblue")
ax2.set_ylim(-30, 5)
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("Cumulative return (%)")
ax.set_title("TW_02 — pre-funding the 30% redemption with a cash sleeve")
ax.legend(loc="lower right", fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "12_tw02_liquidity.png", dpi=110, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ fig 3: TW_03
wk_cop = mm["usd_cop"].pct_change(5).dropna() * 100
cop_ret = mm["usd_cop"].pct_change().reindex(rets.index).fillna(0)
pr02_cop = (1 + pr02) * (1 + cop_ret) - 1
shock = pd.Series(0.0, index=pr02_cop.index); shock.iloc[-1] = 0.08
cum_shock = (1 + pr02_cop + shock).cumprod()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
ax.hist(wk_cop, bins=40, color="darkorange", alpha=0.8, label="observed weekly Δ USD/COP")
ax.axvline(8, color="red", lw=2, ls="--", label="TW_03 shock: +8% (≈11σ)")
ax.set_xlabel("Weekly change in USD/COP (%)")
ax.set_title("TW_03 — COP depreciation vs observed history")
ax.legend(); ax.grid(alpha=0.3)
ax.set_xlim(-3, 9)

ax = axes[1]
ax.plot(cum02.index, (cum02 - 1) * 100, lw=1.2, label="CL_02 in USD terms")
ax.plot((1 + pr02_cop).cumprod().index, ((1 + pr02_cop).cumprod() - 1) * 100,
        lw=1.2, label="CL_02 in COP terms (observed FX)")
ax.plot(cum_shock.index, (cum_shock - 1) * 100, lw=1.6, ls="--", color="red",
        label="COP terms + TW_03 shock (+8% cushion)")
ax.axhline(0, color="k", lw=0.6)
ax.set_ylabel("Cumulative return (%)")
ax.set_title("TW_03 — for a COP-based client the shock is a tailwind")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "13_tw03_cop_shock.png", dpi=110, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ fig 4: combined dashboard
stress = rets.loc["2026-02-09":"2026-02-20"]
ports = {
    "CL_01\n(tol −22%)": ({"VF_A06": .2, "VF_A04": .2, "VF_A05": .2, "VF_A02": .2, "VF_A01": .2}, -22),
    "CL_02 low-vol\n(tol −10%)": (w02, -10),
    "CL_02 70/30\n(tol −10%)": (w02c, -10),
    "CL_03\n(tol −15%)": ({"VF_A01": .2, "VF_A04": .2, "VF_A06": .2, "VF_A07": .2, "VF_A08": .2}, -15),
}
fig, ax = plt.subplots(figsize=(11, 5.5))
xpos = np.arange(len(ports))
vals, tols = [], []
for name, (w, tol) in ports.items():
    pr = stress[list(w)].mul(pd.Series(w), axis=1).sum(axis=1)
    vals.append(((1 + pr).prod() - 1) * 100)
    tols.append(tol)
bars = ax.bar(xpos, vals, width=0.55,
              color=["#2ca02c" if v > t else "#d62728" for v, t in zip(vals, tols)])
for i, (v, t) in enumerate(zip(vals, tols)):
    ax.plot([i - 0.35, i + 0.35], [t, t], color="k", ls="--", lw=1.4)
    ax.text(i, v - 0.5, f"{v:+.1f}%", ha="center", fontsize=10, fontweight="bold")
    ax.text(i + 0.38, t, f"tol {t}%", fontsize=8, va="center")
ax.set_xticks(xpos, list(ports.keys()), fontsize=9)
ax.set_ylabel("2-week stress replay (%)")
ax.set_title("Combined twist stress replay (Feb-2026 analog): all portfolios stay within tolerance\n"
             "CL_02 in COP terms incl. TW_03 shock: low-vol +3.9%, 70/30 +5.1%")
ax.grid(alpha=0.3)
ax.set_ylim(min(tols) - 3, 2)
fig.tight_layout()
fig.savefig(FIG / "14_twist_combined_dashboard.png", dpi=110, bbox_inches="tight")
plt.close(fig)

print("Saved: 11_tw01_rate_shock.png, 12_tw02_liquidity.png, 13_tw03_cop_shock.png, 14_twist_combined_dashboard.png")
