# Credicorp Capital — "Value Finders" Data Hackathon
## Exploratory Data Analysis Report

**Universe:** 8 LatAm/US-listed equities (VF_A01–VF_A08) · 8 issuers · 3 client profiles · 5 corporate/macro events
**Windows:** daily prices & macro 2025-08-01 → 2026-08-14 · intraday 10-min bars 2020-01-02 → 2026-08-14 · fundamentals 2024-Q3 → 2026-Q2

All results are reproducible from the scripts in `analysis/` (run order: `01_inventory.py`, `01b_anomalies.py`, `02_dimensions_and_daily.py`, `04_intraday.py`, `05_macro.py`, `06_fundamentals.py`, `07_integration.py`, `08_client_screening.py`; shared cleaning logic in `clean.py`).

---

## 1. Dataset inventory

| File | Rows | Grain | Content |
|---|---|---|---|
| `01_market_prices_raw.csv` | 2,175 | asset × day | OHLCV, 8 assets, ~1 year |
| `01_market_prices_raw_expanded.csv` | 538,836 | asset × 10-min bar | OHLCV, 8 assets, ~6.6 years (1,727 days × 39 bars) |
| `02_macro_raw.csv` | 271 | day | US 10Y yield, US inflation, 4 FX pairs, market factor, risk regime |
| `03_fundamentals_raw.csv` | 65 | issuer × quarter | revenue, EBITDA, net income, debt, cash |
| `04_asset_reference.csv` | 8 | asset | issuer link, name, sector, country, market, currency |
| `05_client_profiles.csv` | 3 | client | risk tolerance, horizon, drawdown tolerance, constraints |
| `06_events.csv` | 5 | event | dated events scoped to assets or a sector |

The 8 assets span **8 distinct sectors and 5 countries** (Colombia ×2, Peru ×2, US ×2, Mexico, Chile) — a deliberately diversification-friendly universe. All prices in USD.

---

## 2. Data-quality findings & cleaning rules applied

The raw files contain **intentional dirt**. Everything below is fixed in `analysis/clean.py`:

| # | Issue | Where | Fix |
|---|---|---|---|
| 1 | Malformed asset IDs: `VF-A1`, `VFA03`, `VF_A6`, `VF-A4`, `VF-A6` | both price files | mapped to canonical `VF_A0x` |
| 2 | Malformed issuer ID `ISS04` | fundamentals | mapped to `ISS_04` |
| 3 | Mixed date formats: `MM/DD/YYYY` rows among ISO dates (4 rows daily) | prices | mixed-format parser |
| 4 | Quarter label `Q4-2024` instead of a date | fundamentals (ISS_02) | parsed to 2024-12-31 |
| 5 | **Duplicate period for ISS_02** (proper `2024-12-31` row + `Q4-2024` row with *different* values); ISS_02 also **lacks 2025-06-30** | fundamentals | kept explicitly-dated row; YoY growth computed on matched quarters only |
| 6 | Numbers as text: volumes like `3635.6K`, revenue `1,845.7` | prices, fundamentals | suffix/separator-aware parser |
| 7 | Exact duplicate rows | daily (7), intraday (12), fundamentals (1) | dropped |
| 8 | Missing `currency` (4 daily / 35 intraday) | prices | filled `USD` (whole universe is USD) |
| 9 | Missing `close` (24 intraday bars) | intraday | filled with high/low midpoint |
| 10 | **`us_inflation_yoy` 95% missing** — it is a monthly series on a daily grid | macro | forward-filled |
| 11 | **Corrupted close: VF_A06 2026-03-23 = 3,589.00** vs high 35.92 (a ×100-type bad tick; open/high/low and the next day are normal) | daily prices | OHLC values outside the [low, high] band are nulled and interpolated |
| 12 | Missing `cash_usd_m` (ISS_07 2025-09-30), missing volumes (3 daily / 30 intraday) | — | left as NaN, immaterial |

> ⚠️ **Critical cross-file inconsistency:** the daily file and the intraday file **do not agree** in the overlap window. Median close discrepancies range from +0.7% (VF_A01) to **+24.7% (VF_A05, up to 58% on single days)**; volumes also differ (daily ≈ 73–107% of summed intraday). The two files must be treated as **independent sources** — use the daily file for the recent year and the intraday file only for long-history/intraday microstructure analysis, never spliced together.

---

## 3. Market analysis (daily, cleaned)

| Asset | Sector | Country | Tot. ret. | Ann. vol | Max DD | Avg daily $ value |
|---|---|---|---|---|---|---|
| VF_A05 Aurora Health | Health Care | US | **+31.9%** | 24.0% | −13.5% | $160m |
| VF_A04 Lima Financial | Financials | PE | **+20.5%** | 28.2% | −17.4% | $124m |
| VF_A01 Andes Consumer | Cons. Staples | CO | −10.0% | 20.1% | −27.4% | $101m |
| VF_A02 Pacifica Digital | Technology | PE | −13.8% | **45.2%** | **−55.4%** | $175m |
| VF_A08 Atlas Utilities | Utilities | US | −14.2% | **15.4%** | −22.2% | $75m |
| VF_A06 Norte Industrials | Industrials | MX | −22.4% | 33.4% | −37.1% | $66m |
| VF_A03 Cordillera Energy | Energy | CO | −26.5% | 34.9% | −42.5% | $59m |
| VF_A07 Sierra Materials | Materials | CL | −26.7% | 38.3% | −36.2% | $52m |

- **VF_A02 is a boom-bust story**: +80% by Nov-2025, then −55% peak-to-trough during the Feb-2026 stress (see §5–6).
- Winners are **quality defensive-growth** (Health, Financials); losers are **cyclicals/commodity** (Energy, Materials, Industrials).
- Return correlations are low (avg ≈ 0.15; max 0.26 VF_A02–VF_A06) → **real diversification available** inside the universe.
- All assets are liquid enough for institutional tickets (≥ $52m/day traded value).

Figures: `figures/02_price_panels.png`, `figures/02_cumulative.png`, `figures/02_correlations.png`.

## 4. Intraday structure

- Extremely regular: **39 bars/day, 09:30–15:50**, 1,727 sessions per asset, no gaps; classic U-shaped volume curve (`figures/04_intraday_volume_curve.png`).
- 2020–2026 history enables long-horizon backtests — but only against itself, given the daily-file inconsistency (§2).

## 5. Macro & regimes

- **Stress:** 2026-02-09 → 2026-02-20 (10d) · **Recovery:** 2026-03-02 → 2026-03-13 (10d) · otherwise Normal.
- Stress-period total returns: **VF_A02 −23.3%**, VF_A06 −11.2%, VF_A07 −8.4%, VF_A04 −6.2%; **VF_A01 +3.9%** and VF_A03 0.0% held up → Consumer Staples/Energy were the hedges.
- Sensitivity to `market_factor` (beta-like): VF_A04 0.49 > VF_A06 0.46 > VF_A05 0.44 > VF_A02 0.43 > VF_A03 0.41 > VF_A07 0.37 > VF_A01 0.28 > VF_A08 0.29.
- FX over the window: **USD/CLP +7.2%**, USD/COP +2.6% (USD strength), USD/PEN −1.2%, USD/MXN −1.2%. US 10Y 4.35% → 4.10%; inflation 3.0% → 2.8% (monthly series, ffilled).
- COP-CLP co-move 0.74; yield–inflation 0.90 (regime-driven).

Figure: `figures/05_macro.png`.

## 6. Fundamentals (LTM to 2026-Q2, matched-quarter YoY)

| Asset | Rev LTM ($m) | Rev growth | EBITDA margin | Net margin | Net debt/EBITDA |
|---|---|---|---|---|---|
| VF_A06 Norte Industrials | 12,000 | **+17.9%** | 15% | 8% | **0.68× (highest)** |
| VF_A03 Cordillera Energy | 13,471 | +9.1% | 12% | 6% | 0.01× |
| VF_A01 Andes Consumer | 8,559 | +9.0% | **32%** | **19%** | 0.27× |
| VF_A05 Aurora Health | 8,524 | +8.5% | 27% | 16% | 0.31× |
| VF_A04 Lima Financial | 17,992 | +7.8% | 31% | 18% | 0.29× |
| VF_A02 Pacifica Digital | 12,383 | +6.7%* | 28% | 15% | 0.23× |
| VF_A08 Atlas Utilities | 8,434 | +6.9% | 13% | 8% | **−0.24× (net cash)** |
| VF_A07 Sierra Materials | 21,156 | +3.9% | 21% | 12% | 0.12× |

\* matched quarters (ISS_02 missing 2025-Q2). Figure: `figures/06_fundamentals.png`.

## 7. Event study (abnormal returns vs market factor)

| Date | Target | Event | AR day-0 | CAR 0→+5d |
|---|---|---|---|---|
| 2026-02-10 | VF_A02 | Cloud supplier outage (High) | +0.6% | **−16.7%** |
| 2026-04-06 | VF_A03 | Energy margin improvement (Med) | +3.0% | +3.6% |
| 2026-05-18 | VF_A04 | Earnings beat (Med) | −0.9% | −0.2% |
| 2026-06-08 | VF_A07 | External demand weakness (High) | −0.9% | **−7.6%** |
| 2026-07-21 | Technology sector | Growth-multiple repricing (Med) | −1.2% | −3.8% |

High-severity operational/demand events show **multi-day drift** (impact materializes over the following week, not on day 0) — a tradable pattern. Figure: `figures/07_event_study.png`.

## 8. "Value finder" synthesis

Composite z-score = growth + margin + low leverage + contrarian price (beaten-down scores higher):

1. **VF_A01 Andes Consumer** — growing +9%, best margins (32%), low leverage, price −10%: the cleanest *quality-at-a-discount*.
2. **VF_A08 Atlas Utilities** — net-cash balance sheet, lowest vol, price −14%.
3. **VF_A03 Cordillera Energy** — +9% growth, debt-free, price −26.5% (commodity-driven).
4. **VF_A06 Norte Industrials** — fastest grower (+17.9%) and cheapest-looking (−22.4%), but highest leverage → high-risk value.
   Momentum winners VF_A05/VF_A04 rank last on contrarian score (quality is already priced).

Figure: `figures/07_value_map.png`.

## 9. Client-profile screening (illustrative, daily-file backtest)

| Client | Constraint check | Illustrative portfolio | Ann. ret | Vol | Max DD | Tolerance |
|---|---|---|---|---|---|---|
| **CL_01** Crecimiento Global (USD, 18m, high risk) | 5 sectors ≤45% ✓ | EW: A06, A04, A05, A02, A01 | +4.1% | 18.3% | −19.1% | −22% ✓ |
| **CL_02** Patrimonio Estable (COP, 36m, low risk) | high-vol share 0% ≤25% ✓ | EW low-vol only: A08, A01, A05, A04 | +7.3% | 13.5% | **−9.3%** | −10% ✓ |
| **CL_03** Diversificación Regional (PEN, 24m, med risk) | 5 countries, 5 sectors ✓ | EW: A01, A04, A06, A07, A08 | −7.9% | 15.9% | −14.1% | −15% ✓ |

Notes:
- CL_02's 10% drawdown tolerance is **tight**: mixes including >10% cyclicals breach it (tested variant with 10% VF_A03 hit −10.5%). Keep high-vol names near zero or add a cash buffer. USD/COP +2.6% is an FX tailwind for this COP-based client.
- CL_03's equal-weight regional basket passes but is dragged by cyclicals; a quality-tilted variant (A01/A04/A05/A07/A08, 20/20/20/10/10) improves to +5.0% ann., −8.9% maxDD.
- VF_A02 is uninvestable for CL_02/CL_03 (45% vol, −55% DD) and only a satellite position for CL_01.

Figure: `figures/08_client_portfolios.png`.

---

## 10. Caveats & recommended next steps

1. **No share counts / market caps** → true valuation multiples (P/E, EV/EBITDA) are not computable; the value screen uses growth/margin/leverage vs price action as a proxy. If the hackathon provides shares outstanding, upgrade §8 immediately.
2. **Daily vs intraday files are mutually inconsistent** (§2) — pick one source per analysis.
3. Fundamentals are short (8 quarters) and one issuer has a missing quarter; growth rates use matched-quarter sums.
4. Next steps: survivorship-free backtest of the event-drift signal (§7); Markowitz/risk-parity optimization per client using the correlation matrix; FX-hedged variants for CL_02 (COP) and CL_03 (PEN); scenario replay of the Feb-2026 stress for drawdown budgeting.

> **Update:** see `TWIST_REPORT.md` for the scenario analysis of `dataset_twist.csv` (rate shock +65bp, CL_02 liquidity call, COP −8%) — conclusions above hold; CL_02 gains a 30% cash-sleeve refinement.
