"""Stage 7: integration — event impact (abnormal returns), regime performance,
and a price-vs-fundamentals 'value' synthesis."""
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
events = clean.load_events()
macro = clean.load_macro()
fund_score = pd.read_csv(OUT / "06_fundamentals_scorecard.csv")
daily_stats = pd.read_csv(OUT / "02_daily_asset_stats.csv")

wide = px.pivot_table(index="date", columns="asset_id", values="close")
rets = wide.pct_change()
mkt = macro.set_index("date")["market_factor"]

# ---------------------------------------------------------------- event study
print("=" * 78)
print("EVENT STUDY — abnormal returns vs market_factor (AR = r_asset - r_mkt)")
print("=" * 78)
rows = []
for _, ev in events.iterrows():
    d = ev.event_date
    scope = ev.scope
    if scope in wide.columns:
        targets = [scope]
    else:  # sector-level scope, e.g. 'Technology'
        targets = assets.loc[assets.sector == scope, "asset_id"].tolist()
    for t in targets:
        r = rets[t].subtract(mkt.reindex(rets.index)).dropna()
        idx = r.index.searchsorted(d)
        if idx >= len(r):
            continue
        win_pre = r.iloc[max(0, idx - 5):idx]
        win_post = r.iloc[idx:idx + 6]
        ar0 = r.iloc[idx] if idx < len(r) else np.nan
        car_pre = win_pre.sum()
        car_post5 = win_post.sum()
        rows.append({
            "event_date": d.date(), "scope": scope, "target": t,
            "type": ev.event_type, "severity": ev.severity,
            "AR_day0_%": round(ar0 * 100, 2),
            "CAR_pre5_%": round(car_pre * 100, 2),
            "CAR_0_to_+5_%": round(car_post5 * 100, 2),
        })
evdf = pd.DataFrame(rows)
print(evdf.to_string(index=False))
evdf.to_csv(OUT / "07_event_study.csv", index=False)

# plot event windows
fig, axes = plt.subplots(1, len(evdf), figsize=(16, 4), sharey=False)
if len(evdf) == 1:
    axes = [axes]
for ax, (_, ev) in zip(axes, evdf.iterrows()):
    t = ev["target"]
    d = pd.Timestamp(ev["event_date"])
    r = rets[t].subtract(mkt.reindex(rets.index)).dropna()
    idx = r.index.searchsorted(d)
    win = r.iloc[max(0, idx - 10):idx + 11]
    x = range(-len(win) + (len(win) - 11) + 1, 11) if False else range(-10, -10 + len(win))
    car = (1 + win).cumprod() - 1
    ax.plot(range(-(idx - (idx - len(win))), 0) if False else range(len(win)), car.values * 100, marker="o", ms=3)
    ax.axvline(10, color="red", ls="--", lw=1)
    ax.set_title(f"{t} @ {ev['event_date']}\n{ev['type']} ({ev['severity']})", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_xlabel("trading days rel. to event", fontsize=7)
axes[0].set_ylabel("CAR (%)")
fig.suptitle("Cumulative abnormal returns around events (window -10/+10)")
fig.tight_layout()
fig.savefig(FIG / "07_event_study.png", dpi=110)
plt.close(fig)

# ------------------------------------------------------- regime x asset table
print("\n" + "=" * 78)
print("STRESS-EPISODE BEHAVIOUR (2026-02-09 → 2026-02-20) and recovery")
print("=" * 78)
stress = wide.loc["2026-02-09":"2026-02-20"]
rec = wide.loc["2026-03-02":"2026-03-13"]
stress_ret = (stress.iloc[-1] / stress.iloc[0] - 1) * 100
rec_ret = (rec.iloc[-1] / rec.iloc[0] - 1) * 100
rr = pd.DataFrame({"stress_%": stress_ret.round(1), "recovery_%": rec_ret.round(1)})
rr = rr.merge(assets.set_index("asset_id")[["name", "sector"]], left_index=True, right_index=True)
print(rr.to_string())

# ------------------------------------------------- value synthesis scorecard
print("\n" + "=" * 78)
print("VALUE / QUALITY SYNTHESIS (price action vs fundamentals)")
print("=" * 78)
syn = daily_stats[["asset_id", "name", "sector", "country", "total_ret_%",
                   "ann_vol_%", "max_dd_%", "avg_daily_val_USDm"]].merge(
    fund_score[["asset_id", "rev_growth_yoy_%", "ebitda_margin_ltm",
                "net_margin_ltm", "nd_ebitda"]], on="asset_id")
# Simple composite z-score rank: growth + margins - leverage - vol (quality-value tilt)
def z(s):
    return (s - s.mean()) / s.std()
syn["score_growth"] = z(syn["rev_growth_yoy_%"])
syn["score_margin"] = z(syn["ebitda_margin_ltm"])
syn["score_leverage"] = -z(syn["nd_ebitda"])
syn["score_price"] = -z(syn["total_ret_%"])  # contrarian: beaten-down = cheaper
syn["composite"] = (syn.score_growth + syn.score_margin +
                    syn.score_leverage + syn.score_price) / 4
syn = syn.sort_values("composite", ascending=False)
print(syn[["asset_id", "name", "total_ret_%", "rev_growth_yoy_%",
           "ebitda_margin_ltm", "nd_ebitda", "composite"]].round(2).to_string(index=False))
syn.round(3).to_csv(OUT / "07_value_synthesis.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5.5))
sc = ax.scatter(syn["rev_growth_yoy_%"], syn["total_ret_%"],
                s=syn["ebitda_margin_ltm"] * 1200, c=syn["nd_ebitda"],
                cmap="RdYlGn_r", edgecolors="k", alpha=0.85)
for _, r in syn.iterrows():
    ax.annotate(r["asset_id"], (r["rev_growth_yoy_%"], r["total_ret_%"]),
                textcoords="offset points", xytext=(6, 6), fontsize=9)
ax.axhline(0, color="grey", lw=0.6); ax.axvline(0, color="grey", lw=0.6)
ax.set_xlabel("Revenue growth YoY (LTM, matched quarters, %)")
ax.set_ylabel("Price total return (%)")
ax.set_title("Growth vs price return (bubble = EBITDA margin, color = leverage)\n"
             "Top-left = growing but beaten down (potential 'value finds')")
fig.colorbar(sc, label="Net debt / EBITDA")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "07_value_map.png", dpi=110)
plt.close(fig)

print("\nFigures saved: 07_event_study.png, 07_value_map.png")
