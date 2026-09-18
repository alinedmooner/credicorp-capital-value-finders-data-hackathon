# Client-by-Client Situation Report
## Status of each profile after the base analysis + the three twists (2026-08-17)

Reproducible via `analysis/13_client_deep_dive.py`; per-client figures `figures/18_client_CL_0x.png`.
All portfolios are the illustrative equal-weight mixes from the base analysis, backtested on the cleaned daily data (2025-08 → 2026-08).

---

## CL_01 — Crecimiento Global  🟡 ON TRACK, RUNNING HOT

**Profile:** USD base · 18m horizon · high risk · drawdown tolerance −22% · low liquidity need · max 45% per sector.

**Portfolio (EW):** VF_A01, VF_A02, VF_A04, VF_A05, VF_A06 (5 sectors, max 20% each ✓)

| Metric | Value | Assessment |
|---|---|---|
| Total / annualized return | +2.6% / +4.1% | modest for a growth mandate |
| Volatility | 18.3% | appropriate for "Alta" |
| Max drawdown | **−19.1%** | ⚠️ **87% of the −22% budget used** |
| Sharpe | 0.22 | thin |
| Feb-2026 stress replay | −9.3% | comfortable |

**Key structural issue — risk concentration:** VF_A02 is 20% of the money but **36% of the portfolio's volatility** (its own vol is 45%). The growth engine is also the main drawdown driver; VF_A02 alone went through a −55% peak-to-trough.

**Twist exposure:** TW_01 hits two holdings — VF_A06 (20%, most leveraged → refinancing risk) and VF_A02 (20%, long-duration growth). TW_03 irrelevant (USD base). TW_02 not theirs.

**Recommended tune-up (optional):** trim VF_A02 20%→10%, redistribute to A01/A04/A05 → backtest improves to **+4.3% total, maxDD −14.0%** (budget use 87%→64%) — strictly better on both axes. Keep VF_A06 on the rate watch list.

## CL_02 — Patrimonio Estable  🟢 HEALTHY — AND THE TWISTS' MAIN CHARACTER

**Profile:** COP base · 36m horizon · medium-low risk · tolerance −10% · medium liquidity · max 25% in high-vol assets.

**Portfolio (EW low-vol):** VF_A08, VF_A01, VF_A05, VF_A04 (0% high-vol ✓, well under the 25% cap)

| Metric | USD terms | COP terms (their reality) |
|---|---|---|
| Total / ann. return | +7.1% / +7.3% | **+9.8% / +9.8%** |
| Volatility | 13.5% | 14.8% |
| Max drawdown | −9.3% (93% of budget) | ⚠️ **−10.6% — marginally over −10%** |
| Sharpe | 0.54 (best of the three) | — |
| Stress replay | −3.8% | +3.9% incl. TW_03 shock |

**The subtle finding:** in USD the portfolio respects the −10% tolerance, but **in COP terms it briefly breached it (−10.6%)** — FX translation adds volatility even when the FX trend is favorable.

**Their twists:**
- **TW_02 (30% needed in 6 months):** selling takes <1 day (no market-liquidity issue); every rolling 6-month window ended ≥ −1.8%. The fix for both the COP-terms breach and the redemption: **70/30 cash sleeve** → USD maxDD −6.6%, **COP-terms maxDD −8.2%** ✓, still +7.6% annualized in COP.
- **TW_03 (COP −8%):** a *tailwind* — +8% translation gain; unhedged USD is their crisis hedge.

**Verdict:** best-positioned client. Implement the sleeve and everything is within tolerance in *both* currencies.

## CL_03 — Diversificación Regional  🔴 WEAKEST — NEEDS REBALANCING

**Profile:** PEN base · 24m horizon · medium risk · tolerance −15% · ≥3 countries and ≥3 sectors.

**Portfolio (EW):** VF_A01, VF_A04, VF_A06, VF_A07, VF_A08 — 5 countries, 5 sectors ✓ (the diversification rule passes with room)

| Metric | USD terms | PEN terms (their reality) |
|---|---|---|
| Total / ann. return | **−9.3% / −7.9%** | **−10.4% / −8.9%** |
| Volatility | 15.9% | 16.4% |
| Max drawdown | −14.1% (94% of budget) | 🔴 **−17.2% — BREACHES −15%** |
| Sharpe | −0.50 | — |
| Stress replay | −6.4% | — |

**Diagnosis:** the diversification *rule* passes, but the portfolio is economically concentrated in **cyclicals/commodities** (VF_A06 Industrials + VF_A07 Materials = 40% of weight, **60% of the risk**), the year's worst segment. PEN strength (USD/PEN −1.2%) adds a base-currency drag that pushes the drawdown past tolerance.

**Twist exposure:** TW_01 → VF_A06 leverage (20%) and VF_A07 commodity beta (20%). TW_03's COP move doesn't touch them directly, but the same logic in PEN argues for *some* USD unhedged exposure as a hedge — PEN appreciation is currently hurting them.

**Recommended rebalance (rule-compliant):** quality tilt — **VF_A01 25%, VF_A04 25%, VF_A05 20%, VF_A07 15%, VF_A08 15%** (drops VF_A06; still 4 countries, 5 sectors ✓):
→ USD: **+3.1% total, maxDD −11.7%** · PEN: +1.9%, **maxDD −12.1%** ✓ — back inside tolerance in both currencies.

---

## Summary board

| Client | Status | DD budget used (base ccy) | Main action |
|---|---|---|---|
| CL_01 Crecimiento Global | 🟡 on track, hot | 87% (USD) | optional: trim VF_A02 to 10% → 64% |
| CL_02 Patrimonio Estable | 🟢 healthy | 106% in COP → **82% with sleeve** | implement 70/30 cash sleeve (TW_02) |
| CL_03 Diversificación Regional | 🔴 weakest | 115% in PEN → **81% rebalanced** | rebalance to quality tilt, drop VF_A06 |

**Cross-client observation:** tolerances must be checked in the *client's base currency*, not USD — FX translation moved CL_02 and CL_03 across their limits. And VF_A06 (Norte Industrials) is the common thread of fragility: it appears in two portfolios and is the most exposed to TW_01's rate shock.
