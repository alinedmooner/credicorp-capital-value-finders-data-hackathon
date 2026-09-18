"""Stage 2: dimension tables (assets, clients, events) + daily price analytics."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import clean

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"

assets = clean.load_assets()
clients = clean.load_clients()
events = clean.load_events()
px = clean.load_prices_daily()

print("=" * 78)
print("ASSET REFERENCE (8 assets)")
print("=" * 78)
print(assets.to_string(index=False))
print("\nSector x country grid:")
print(assets.groupby(["sector", "country"]).size().to_string())

print("\n" + "=" * 78)
print("CLIENT PROFILES (3)")
print("=" * 78)
for _, r in clients.iterrows():
    print(f"\n{r.client_id} | {r.profile_name} | base={r.base_currency} | horizon={r.horizon_months}m")
    print(f"  risk={r.risk_tolerance}, maxDD={r.max_drawdown_tolerance_pct}%, liquidity={r.liquidity_need}")
    print(f"  priority: {r.priority}")
    print(f"  constraint: {r.constraint}")

print("\n" + "=" * 78)
print("EVENTS (5)")
print("=" * 78)
print(events.to_string(index=False))

# ---------------------------------------------------------------- daily prices
print("\n" + "=" * 78)
print("DAILY PRICE ANALYTICS (cleaned)")
print("=" * 78)

px = px.merge(assets[["asset_id", "name", "sector", "country"]], on="asset_id", how="left")

stats = []
for aid, g in px.groupby("asset_id"):
    g = g.sort_values("date")
    ret = g["close"].pct_change()
    # annualized vol on ~252 trading days
    vol_ann = ret.std() * np.sqrt(252)
    total_ret = g["close"].iloc[-1] / g["close"].iloc[0] - 1
    # max drawdown
    cum = g["close"] / g["close"].iloc[0]
    dd = (cum / cum.cummax() - 1).min()
    adv_usd = (g["close"] * g["volume"]).mean()  # avg daily traded value
    stats.append({
        "asset_id": aid,
        "name": g["name"].iloc[0],
        "sector": g["sector"].iloc[0],
        "country": g["country"].iloc[0],
        "n_days": len(g),
        "first": g["date"].min().date(),
        "last": g["date"].max().date(),
        "px_first": g["close"].iloc[0],
        "px_last": g["close"].iloc[-1],
        "total_ret_%": round(total_ret * 100, 1),
        "ann_vol_%": round(vol_ann * 100, 1),
        "max_dd_%": round(dd * 100, 1),
        "avg_daily_val_USDm": round(adv_usd / 1e6, 1),
        "best_day_%": round(ret.max() * 100, 1),
        "worst_day_%": round(ret.min() * 100, 1),
    })
stats = pd.DataFrame(stats)
print(stats.to_string(index=False))
stats.to_csv(OUT / "02_daily_asset_stats.csv", index=False)

# outlier daily moves (|ret| > 4 sigma per asset)
print("\nOUTLIER DAILY MOVES (|z| > 4 per asset):")
for aid, g in px.groupby("asset_id"):
    g = g.sort_values("date")
    ret = g["close"].pct_change()
    z = (ret - ret.mean()) / ret.std()
    out = g[abs(z) > 4]
    for _, r in out.iterrows():
        print(f"  {aid} {r['date'].date()} close={r['close']} ret={ret.loc[r.name]*100:+.1f}% (z={z.loc[r.name]:+.1f})")

# return correlation matrix
wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change().dropna(how="all")
corr = rets.corr().round(2)
print("\nRETURN CORRELATION MATRIX:")
print(corr.to_string())
corr.to_csv(OUT / "02_return_correlations.csv")

# ------------------------------------------------------------------ figures
fig, axes = plt.subplots(4, 2, figsize=(14, 16), sharex=True)
for ax, (aid, g) in zip(axes.flat, px.groupby("asset_id")):
    g = g.sort_values("date")
    ax.plot(g["date"], g["close"], lw=1)
    nm = g["name"].iloc[0]
    ax.set_title(f"{aid} – {nm}", fontsize=10)
    ax.grid(alpha=0.3)
fig.suptitle("Daily close prices (2025-08 → 2026-08)", y=0.995)
fig.tight_layout()
fig.savefig(FIG / "02_price_panels.png", dpi=110)
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 6))
cum = wide / wide.iloc[0]
for c in cum.columns:
    ax.plot(cum.index, cum[c], lw=1.2, label=c)
ax.legend(ncol=4, fontsize=8)
ax.set_title("Cumulative performance (rebased to 1.0)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "02_cumulative.png", dpi=110)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr)), corr.index)
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center", fontsize=7)
fig.colorbar(im)
ax.set_title("Daily return correlations")
fig.tight_layout()
fig.savefig(FIG / "02_correlations.png", dpi=110)
plt.close(fig)

print("\nFigures saved: 02_price_panels.png, 02_cumulative.png, 02_correlations.png")
