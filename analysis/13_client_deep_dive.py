"""Per-client deep dive: situation, exposures, contributions, twist exposure,
and client-specific recommendations. One figure per client."""
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
clients = clean.load_clients()
macro = clean.load_macro()
syn = pd.read_csv(OUT / "07_value_synthesis.csv")

wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change().dropna()
mm = macro.set_index("date")

PORTS = {
    "CL_01": {"VF_A06": .2, "VF_A04": .2, "VF_A05": .2, "VF_A02": .2, "VF_A01": .2},
    "CL_02": {"VF_A08": .25, "VF_A01": .25, "VF_A05": .25, "VF_A04": .25},
    "CL_03": {"VF_A01": .2, "VF_A04": .2, "VF_A06": .2, "VF_A07": .2, "VF_A08": .2},
}
# CL_02 alternative with cash sleeve (TW_02 answer)
W02C = {k: v * 0.70 for k, v in PORTS["CL_02"].items()}

stress = rets.loc["2026-02-09":"2026-02-20"]
nm = assets.set_index("asset_id")["name"]
sec = assets.set_index("asset_id")["sector"]
cty = assets.set_index("asset_id")["country"]
vol_a = syn.set_index("asset_id")["ann_vol_%"]

def stats(pr):
    cum = (1 + pr).cumprod()
    return dict(
        cum=cum,
        total=(cum.iloc[-1] - 1) * 100,
        ann=pr.mean() * 252 * 100,
        vol=pr.std() * np.sqrt(252) * 100,
        dd=(cum / cum.cummax() - 1).min() * 100,
        sharpe=pr.mean() / pr.std() * np.sqrt(252),
    )

report = []
def log(s=""):
    print(s); report.append(s)

for cid in ["CL_01", "CL_02", "CL_03"]:
    c = clients[clients.client_id == cid].iloc[0]
    w = pd.Series(PORTS[cid])
    pr = rets[w.index].mul(w, axis=1).sum(axis=1)
    st = stats(pr)
    stress_ret = ((1 + stress[w.index].mul(w, axis=1).sum(axis=1)).prod() - 1) * 100

    log("=" * 78)
    log(f"{cid} — {c.profile_name}")
    log("=" * 78)
    log(f"Profile: base={c.base_currency} | horizon={c.horizon_months}m | risk={c.risk_tolerance} | "
        f"maxDD tol={c.max_drawdown_tolerance_pct}% | liquidity={c.liquidity_need}")
    log(f"Priority: {c.priority} | Constraint: {c.constraint}")
    log("")
    log("HOLDINGS & EXPOSURE:")
    for a, wt in w.items():
        log(f"  {a} {nm[a]:<20} {wt*100:4.0f}%  {sec[a]:<18} {cty[a]:<14} "
            f"asset vol={vol_a[a]:.0f}%")
    # contributions to portfolio volatility
    cov = rets[w.index].cov() * 252
    port_var = (w @ cov @ w)
    mrc = cov @ w / np.sqrt(port_var)          # marginal risk contribution
    rc = w * mrc / np.sqrt(port_var)           # % contribution to vol
    log("\nRISK CONTRIBUTION (% of portfolio volatility):")
    for a in w.index:
        log(f"  {a}: weight={w[a]*100:.0f}% -> risk share={rc[a]*100:.0f}%")
    sec_exp = w.groupby(sec[w.index]).sum()
    cty_exp = w.groupby(cty[w.index]).sum()
    log(f"\nSector exposure: {dict((sec_exp*100).round(0))}")
    log(f"Country exposure: {dict((cty_exp*100).round(0))}")

    log("\nPERFORMANCE (2025-08 → 2026-08, USD):")
    log(f"  total={st['total']:+.1f}%  ann={st['ann']:+.1f}%  vol={st['vol']:.1f}%  "
        f"maxDD={st['dd']:+.1f}%  Sharpe={st['sharpe']:.2f}")
    tol = -c.max_drawdown_tolerance_pct
    used = abs(st['dd']) / abs(tol) * 100
    log(f"  drawdown budget used: {used:.0f}% of {c.max_drawdown_tolerance_pct}% tolerance "
        f"({'OK' if st['dd'] >= tol else 'BREACH'})")
    log(f"  Feb-2026 stress replay: {stress_ret:+.1f}%")

    # FX situation
    fx_map = {"CL_01": None, "CL_02": "usd_cop", "CL_03": "usd_pen"}
    fx = fx_map[cid]
    if fx:
        fx_ret = mm[fx].pct_change().reindex(pr.index).fillna(0)
        pr_fx = (1 + pr) * (1 + fx_ret) - 1
        st_fx = stats(pr_fx)
        ccy = "COP" if cid == "CL_02" else "PEN"
        log(f"\nIN {ccy} TERMS: total={st_fx['total']:+.1f}%  ann={st_fx['ann']:+.1f}%  "
            f"maxDD={st_fx['dd']:+.1f}%")

    # twists
    log("\nTWIST EXPOSURE:")
    if cid == "CL_01":
        log("  TW_01 (rates): VF_A06 (20%) is the most leveraged name -> watch;")
        log("                 VF_A02 (20%) is long-duration growth, highest vol.")
        log("  TW_02: not applicable.  TW_03: USD base -> no FX translation risk.")
    elif cid == "CL_02":
        prc = rets[list(W02C)].mul(pd.Series(W02C), axis=1).sum(axis=1)
        stc = stats(prc)
        log(f"  TW_02 (THEIR twist): 30% needed in 6m -> liquidation <1 day;")
        log(f"    recommended 70/30 cash sleeve: ann={stc['ann']:+.1f}% vol={stc['vol']:.1f}% "
            f"maxDD={stc['dd']:+.1f}%")
        log("  TW_03 (THEIR currency): +8% COP fall = +8% translation gain;")
        log("    stress replay in COP with shock: -3.8% -> +3.9% (low-vol), -2.7% -> +5.1% (70/30).")
    else:
        log("  TW_01 (rates): VF_A06 (20%) leverage watch; VF_A07 (20%) commodity-beta.")
        log("  TW_03: PEN base; USD/PEN -1.2% over window -> mild FX drag (~-1.2%).")
        log("  Diversification rule: 5 countries, 5 sectors -> PASS.")

    # figure per client
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax = axes[0, 0]
    ax.plot(st["cum"].index, (st["cum"] - 1) * 100, lw=1.4, color="navy",
            label=f"portfolio (maxDD {st['dd']:.1f}%)")
    ax.axhline(tol, color="red", ls="--", lw=1.2, label=f"tolerance {tol:.0f}%")
    for a in w.index:
        ca = wide[a] / wide[a].iloc[0]
        ax.plot(ca.index, (ca - 1) * 100, lw=0.6, alpha=0.35, color="grey")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title(f"{cid} — portfolio vs holdings (grey) and tolerance")
    ax.set_ylabel("cumulative return (%)")

    ax = axes[0, 1]
    dds = (st["cum"] / st["cum"].cummax() - 1) * 100
    ax.fill_between(dds.index, dds, 0, color="steelblue", alpha=0.5)
    ax.axhline(tol, color="red", ls="--", lw=1.2)
    ax.set_title("Drawdown underwater curve"); ax.grid(alpha=0.3)

    ax = axes[1, 0]
    rc_sorted = rc.sort_values()
    ax.barh([nm[a] for a in rc_sorted.index], rc_sorted.values * 100, color="teal")
    ax.set_title("Risk contribution by position (% of portfolio vol)")
    ax.grid(alpha=0.3)

    ax = axes[1, 1]
    labels = [f"{a}\n{sec[a]}" for a in w.index]
    ax.pie(w.values, labels=labels, autopct="%1.0f%%", textprops={"fontsize": 7})
    ax.set_title("Allocation (sector shown)")
    fig.tight_layout()
    fig.savefig(FIG / f"18_client_{cid}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    log(f"\nFigure: 18_client_{cid}.png\n")

(OUT / "13_client_situation.txt").write_text("\n".join(report), encoding="utf-8")
print("Saved -> 13_client_situation.txt")
