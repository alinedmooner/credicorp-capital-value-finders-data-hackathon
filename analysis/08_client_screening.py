"""Stage 8: client-profile screening — map each client's constraints to asset
characteristics and test illustrative portfolios against drawdown tolerances."""
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

HIGH_VOL_THRESHOLD = 30.0  # ann_vol_% cutoff for 'high volatility' (CL_02 rule)

syn["high_vol"] = syn["ann_vol_%"] > HIGH_VOL_THRESHOLD
print("=" * 78)
print("ASSET SCREENING BOARD")
print("=" * 78)
board = syn[["asset_id", "name", "sector", "country", "ann_vol_%", "max_dd_%",
             "total_ret_%", "rev_growth_yoy_%", "ebitda_margin_ltm",
             "nd_ebitda", "avg_daily_val_USDm", "high_vol", "composite"]]
print(board.round(2).to_string(index=False))

def port_stats(weights: dict):
    w = pd.Series(weights)
    pr = rets[w.index].mul(w, axis=1).sum(axis=1)
    cum = (1 + pr).cumprod()
    return {
        "ann_ret_%": round(pr.mean() * 252 * 100, 1),
        "ann_vol_%": round(pr.std() * np.sqrt(252) * 100, 1),
        "max_dd_%": round((cum / cum.cummax() - 1).min() * 100, 1),
        "total_ret_%": round((cum.iloc[-1] - 1) * 100, 1),
    }, cum

print("\n" + "=" * 78)
print("CLIENT-BY-CLIENT SCREENING")
print("=" * 78)

portfolios = {}

# ---- CL_01: growth, high risk, max 45% per sector, maxDD tol 22%
c = clients.iloc[0]
print(f"\n### {c.client_id} {c.profile_name} ({c.base_currency}, {c.horizon_months}m, "
      f"risk={c.risk_tolerance}, maxDD={c.max_drawdown_tolerance_pct}%)")
print(f"    constraint: {c.constraint}")
# pick: top growth/composite names, all distinct sectors anyway (8 sectors x 8 assets)
sel = ["VF_A06", "VF_A04", "VF_A05", "VF_A02", "VF_A01"]  # growth + quality tilt
w = {a: 0.20 for a in sel}
st, cum1 = port_stats(w)
portfolios["CL_01"] = (w, st, cum1)
print(f"    selected (equal weight): {sel}")
print(f"    portfolio: {st}  -> maxDD within 22% tolerance? {st['max_dd_%'] >= -22}")

# ---- CL_02: conservative, COP base, max 25% in high-vol assets, maxDD tol 10%
c = clients.iloc[1]
print(f"\n### {c.client_id} {c.profile_name} ({c.base_currency}, {c.horizon_months}m, "
      f"risk={c.risk_tolerance}, maxDD={c.max_drawdown_tolerance_pct}%)")
print(f"    constraint: {c.constraint}")
low_vol = syn[~syn.high_vol].sort_values("composite", ascending=False)["asset_id"].tolist()
print(f"    low-vol universe (vol<=30%): {low_vol}")
# 75% low-vol defensives + <=25% one high-vol name for yield
w = {"VF_A08": 0.30, "VF_A01": 0.25, "VF_A05": 0.20, "VF_A04": 0.15, "VF_A03": 0.10}
hv = sum(v for k, v in w.items() if syn.set_index("asset_id").loc[k, "high_vol"])
st, cum2 = port_stats(w)
portfolios["CL_02"] = (w, st, cum2)
print(f"    selected: {w}")
print(f"    high-vol share: {hv*100:.0f}% (limit 25%)")
print(f"    portfolio: {st}  -> maxDD within 10% tolerance? {st['max_dd_%'] >= -10}")
print(f"    FX note: USD/COP +2.6% over window -> USD assets gain ~2.6% in COP terms")

# ---- CL_03: regional diversification, PEN base, >=3 countries & >=3 sectors
c = clients.iloc[2]
print(f"\n### {c.client_id} {c.profile_name} ({c.base_currency}, {c.horizon_months}m, "
      f"risk={c.risk_tolerance}, maxDD={c.max_drawdown_tolerance_pct}%)")
print(f"    constraint: {c.constraint}")
w = {"VF_A01": 0.20, "VF_A04": 0.20, "VF_A06": 0.20, "VF_A07": 0.20, "VF_A08": 0.20}
countries = assets.set_index("asset_id").loc[list(w), "country"].unique()
sectors = assets.set_index("asset_id").loc[list(w), "sector"].unique()
st, cum3 = port_stats(w)
portfolios["CL_03"] = (w, st, cum3)
print(f"    selected: {list(w)}")
print(f"    countries ({len(countries)}): {list(countries)} | sectors ({len(sectors)}): {list(sectors)}")
print(f"    portfolio: {st}  -> maxDD within 15% tolerance? {st['max_dd_%'] >= -15}")
print(f"    FX note: USD/PEN -1.2% -> slight FX drag for PEN-based investor")

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(figsize=(12, 6))
for name, (w, st, cum) in portfolios.items():
    ax.plot(cum.index, cum.values, lw=1.4, label=f"{name} (maxDD {st['max_dd_%']}%)")
for tol, lbl in [(-22, "CL_01 tol -22%"), (-15, "CL_03 tol -15%"), (-10, "CL_02 tol -10%")]:
    pass
ax.axhline(1 - 0.22, color="C0", ls=":", lw=0.8)
ax.axhline(1 - 0.15, color="C1", ls=":", lw=0.8)
ax.axhline(1 - 0.10, color="C2", ls=":", lw=0.8)
ax.legend(); ax.grid(alpha=0.3)
ax.set_title("Illustrative client portfolios (cumulative, rebased) vs drawdown tolerances (dotted)")
fig.tight_layout()
fig.savefig(FIG / "08_client_portfolios.png", dpi=110)
plt.close(fig)

print("\nFigure saved: 08_client_portfolios.png")
