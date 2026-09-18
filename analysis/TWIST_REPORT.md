# Twist Analysis — `dataset_twist.csv`
## Do the three post-window events change the conclusions? (Spoiler: mostly no — but they refine CL_02's implementation)

The twist file contains **3 events effective 2026-08-17**, three days after the data window closes (2026-08-14). Each was stress-tested against the cleaned datasets and the stage-8 client portfolios. Reproducible via `analysis/10_twist_analysis.py`; figure: `figures/10_twist_analysis.png`.

| # | Twist | Required action | Verdict |
|---|---|---|---|
| TW_01 | US 10Y **+65bp in a week** (inflation surprise) | Re-check rate sensitivity / valuation | **Does not change selection** — no measurable rate sensitivity exists in the data; manage via leverage & stress analog |
| TW_02 | **CL_02 needs 30% of the portfolio in 6 months** | Re-check recommendation vs liquidity | **Recommendation stays**, add a 30% cash/T-bill sleeve (liquidity itself is a non-issue) |
| TW_03 | **COP −8% vs USD in days** | Impact for COP-based client (CL_02) | **It helps CL_02** — unhedged USD exposure is a cushion, not a risk |

---

## TW_01 — The +65bp rate shock

**How extreme is it?** Within the observed window, weekly yield changes had σ = 1.2bp (max +2.5bp). A +65bp week is a **~54σ tail event** — the dataset contains nothing remotely like it, so the honest answer has two parts:

**1. What the data can say: nothing reliable.** Regressing daily asset returns on daily yield changes gives R² ≤ 1.3% for every asset — statistically indistinguishable from zero. Point estimates are even *positive* for 7 of 8 assets (implausible as economics, typical of noise). **Rate betas are not identifiable from this dataset**; any model claiming precise sensitivity would be overfitting.

**2. What theory + the stress analog say.** Since the shock arrives via an inflation surprise, it would almost surely coincide with a risk-off regime — the Feb-2026 stress episode is the better guide than regression:
- **Most vulnerable:** VF_A06 Norte Industrials — highest leverage (net debt/EBITDA 0.68× LTM, quarterly ratio ~2.5–3.1×) → refinancing-cost exposure; also the only negative in-sample response to the largest observed yield rises. VF_A02 Pacifica Digital — long-duration growth cash flows, already the weakest trend (−0.18%/day) and highest vol (45%).
- **Relative winners:** VF_A04 Lima Financial — banks typically gain from higher rates via NIM expansion (+20.5% total return, best positive trend). VF_A03 Cordillera Energy — inflation-linked commodity revenues, debt-free balance sheet.
- **Value-synthesis impact:** the top picks (VF_A01, VF_A08, VF_A03) share exactly the traits that survive rate shocks — low/no leverage, pricing power, short cash-flow duration. **No ranking change.**

> Action: keep selections; flag VF_A06's leverage as the transmission channel to watch; if a rate scenario must be priced, use the Feb-2026 replay (below), not the fitted betas.

## TW_02 — CL_02's 30% liquidity need in 6 months

Tested on the compliant CL_02 portfolio (equal-weight VF_A08 / VF_A01 / VF_A05 / VF_A04):

**Market liquidity is a non-issue.** Raising $30m from a $100m portfolio at 20% of average daily volume takes **≤ 0.5 trading days** per position (all assets trade $52–175m/day). The constraint "liquidity_need = Media" was already satisfied with room to spare.

**Horizon risk is the real question** — will the portfolio be above water when the money is needed?
- Rolling 6-month returns over the window: mean **+5.4%**, worst **−1.8%**.
- Worst drawdown inside *any* 6-month window: **−9.3%** — and **0% of windows** breached the −10% tolerance.

**Recommended redesign (prudent, not required):** carve the future redemption out now —
**30% cash/T-bills + 70% current low-vol mix**:

| Variant | Ann. ret | Vol | Max DD | vs −10% tolerance |
|---|---|---|---|---|
| Current low-vol mix | +7.3% | 13.5% | −9.3% | ✓ (thin margin) |
| **70/30 cash sleeve** | +5.1% | 9.5% | **−6.6%** | ✓ (comfortable) |

The sleeve costs ~2.2pp of expected annual return and buys a 3.4x thicker drawdown cushion plus guaranteed availability of the 30% — the right trade for "Preservación + crecimiento moderado".

## TW_03 — COP depreciation of 8%

**Tail size:** weekly USD/COP changes had σ = 0.70% (max +2.2%) → +8% ≈ **11σ**.

**Direction of the impact: positive for CL_02.** The portfolio is 100% USD-denominated and CL_02's base currency is COP, so a COP crash produces a **+8% one-off translation gain** in COP terms. Replaying the Feb-2026 stress in COP terms with the shock:

| CL_02 variant | Stress replay (USD) | Same, in COP with +8% FX |
|---|---|---|
| Low-vol mix | −3.8% | **+3.9%** |
| 70/30 sleeve | −2.7% | **+5.1%** |

**No hidden equity-FX linkage:** correlations of daily asset returns with USD/COP moves are all ≤ |0.10| — including the two Colombian names (VF_A01 −0.10, VF_A03 +0.03) — so the equity leg does not systematically amplify or offset the FX move.

> Action: **keep the USD exposure unhedged** for CL_02. In COP terms it acts as a crisis hedge (COP tends to weaken exactly when risk assets wobble). Observed-window evidence: COP terms lifted ann. return from +7.3% to +9.8%.

## Combined stress replay (all twists' economic content at once)

Feb-2026 episode (2 weeks) applied to each client portfolio:

| Portfolio | 2-week stress | Within tolerance? |
|---|---|---|
| CL_01 (growth mix) | −9.3% | ✓ (tol. −22%) |
| CL_02 low-vol | −3.8% | ✓ (tol. −10%) |
| CL_02 70/30 sleeve | −2.7% | ✓✓ |
| CL_03 (regional EW) | −6.4% | ✓ (tol. −15%) |

## Bottom line — what changes, what holds

**Holds:** the value ranking (VF_A01 > VF_A08 > VF_A03), all three client portfolios, the exclusion of VF_A02 from conservative mandates, and the unhedged-USD stance for CL_02.

**Changes (implementation detail, not strategy):**
1. CL_02 should pre-fund the known redemption with a **30% cash/T-bill sleeve** (maxDD improves −9.3% → −6.6%).
2. **VF_A06 goes on a watch list** — its leverage is the credible transmission channel for TW_01; any rate-driven derating hits it first (relevant for CL_01 and CL_03, where it is a 20% position).
3. Rate-sensitivity modeling from this dataset alone is **statistically unsupported** (R² ≤ 1.3%) — a data limitation to disclose, not a number to trust.
