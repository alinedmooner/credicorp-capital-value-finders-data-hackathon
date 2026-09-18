"""Stage 6: fundamentals — growth, margins, leverage, quality per issuer."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import clean

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"

f = clean.load_fundamentals()
assets = clean.load_assets()
f = f.merge(assets[["issuer_id", "asset_id", "name", "sector"]], on="issuer_id", how="left")

print("=" * 78)
print("FUNDAMENTALS COVERAGE")
print("=" * 78)
print(f"rows: {len(f)}, periods: {sorted(f.period_end.dt.date.unique())}")
print(f.groupby("issuer_id").size().to_string())

# derived metrics
f["ebitda_margin"] = f["ebitda_usd_m"] / f["revenue_usd_m"]
f["net_margin"] = f["net_income_usd_m"] / f["revenue_usd_m"]
f["net_debt"] = f["debt_usd_m"] - f["cash_usd_m"]
f["net_debt_ebitda"] = f["net_debt"] / f["ebitda_usd_m"]

# QoQ revenue growth per issuer
f = f.sort_values(["issuer_id", "period_end"])
f["rev_growth_qoq"] = f.groupby("issuer_id")["revenue_usd_m"].pct_change()

# LTM aggregates for the last 4 quarters available (2025-09-30 .. 2026-06-30)
last4 = f[f.period_end >= "2025-09-30"]
ltm = last4.groupby(["issuer_id", "asset_id", "name", "sector"], as_index=False).agg(
    rev_ltm=("revenue_usd_m", "sum"),
    ebitda_ltm=("ebitda_usd_m", "sum"),
    ni_ltm=("net_income_usd_m", "sum"),
    debt_last=("debt_usd_m", "last"),
    cash_last=("cash_usd_m", "last"),
)
ltm["ebitda_margin_ltm"] = ltm.ebitda_ltm / ltm.rev_ltm
ltm["net_margin_ltm"] = ltm.ni_ltm / ltm.rev_ltm
ltm["net_debt"] = ltm.debt_last - ltm.cash_last
ltm["nd_ebitda"] = ltm.net_debt / ltm.ebitda_ltm

# YoY growth on MATCHED quarters only (ISS_02 lacks 2025-06-30, so naive
# LTM-vs-prior-LTM would be distorted): compare each quarter of the LTM window
# with the same quarter a year earlier, using only pairs present in both.
f["qoy"] = f.period_end.dt.quarter
f["yr"] = f.period_end.dt.year
cur = f[f.period_end >= "2025-09-30"][["issuer_id", "qoy", "revenue_usd_m", "ebitda_usd_m"]]
pri = f[(f.period_end >= "2024-09-30") & (f.period_end <= "2025-06-30")][
    ["issuer_id", "qoy", "revenue_usd_m", "ebitda_usd_m"]]
pairs = cur.merge(pri, on=["issuer_id", "qoy"], suffixes=("_cur", "_pri"))
growth = pairs.groupby("issuer_id").agg(
    rev_cur=("revenue_usd_m_cur", "sum"), rev_pri=("revenue_usd_m_pri", "sum"),
    ebitda_cur=("ebitda_usd_m_cur", "sum"), ebitda_pri=("ebitda_usd_m_pri", "sum"),
    n_matched=("qoy", "count"))
growth["rev_growth_yoy_%"] = (growth.rev_cur / growth.rev_pri - 1) * 100
growth["ebitda_growth_yoy_%"] = (growth.ebitda_cur / growth.ebitda_pri - 1) * 100
ltm = ltm.drop(columns=[c for c in ltm.columns if c.endswith("_prev")], errors="ignore")
ltm = ltm.merge(growth[["rev_growth_yoy_%", "ebitda_growth_yoy_%", "n_matched"]],
                on="issuer_id", how="left")

cols = ["asset_id", "name", "sector", "rev_ltm", "rev_growth_yoy_%",
        "ebitda_margin_ltm", "net_margin_ltm", "nd_ebitda"]
print("\nLTM FUNDAMENTAL SCORECARD (ending 2026-06-30):")
print(ltm[cols].round(2).sort_values("rev_growth_yoy_%", ascending=False).to_string(index=False))
ltm.round(4).to_csv(OUT / "06_fundamentals_scorecard.csv", index=False)

# margin trend per issuer
print("\nEBITDA margin by quarter:")
marg = f.pivot_table(index="period_end", columns="asset_id", values="ebitda_margin").round(3)
print(marg.to_string())

print("\nNet debt / EBITDA by quarter:")
nd = f.pivot_table(index="period_end", columns="asset_id", values="net_debt_ebitda").round(2)
print(nd.to_string())

# ------------------------------------------------------------------ figures
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for aid, g in f.groupby("asset_id"):
    axes[0, 0].plot(g.period_end, g.revenue_usd_m, marker="o", ms=3, lw=1, label=aid)
axes[0, 0].set_title("Quarterly revenue (USD m)"); axes[0, 0].legend(fontsize=6, ncol=2)
axes[0, 0].grid(alpha=0.3)
for aid, g in f.groupby("asset_id"):
    axes[0, 1].plot(g.period_end, g.ebitda_margin, marker="o", ms=3, lw=1, label=aid)
axes[0, 1].set_title("EBITDA margin"); axes[0, 1].grid(alpha=0.3)
for aid, g in f.groupby("asset_id"):
    axes[1, 0].plot(g.period_end, g.net_debt_ebitda, marker="o", ms=3, lw=1, label=aid)
axes[1, 0].axhline(0, color="k", lw=0.5)
axes[1, 0].set_title("Net debt / EBITDA"); axes[1, 0].grid(alpha=0.3)
s = ltm.sort_values("rev_growth_yoy_%")
axes[1, 1].barh(s.asset_id, s["rev_growth_yoy_%"],
                color=["green" if x > 0 else "red" for x in s["rev_growth_yoy_%"]])
axes[1, 1].set_title("Revenue growth YoY (LTM, %)"); axes[1, 1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "06_fundamentals.png", dpi=110)
plt.close(fig)

print("\nFigure saved: 06_fundamentals.png")
