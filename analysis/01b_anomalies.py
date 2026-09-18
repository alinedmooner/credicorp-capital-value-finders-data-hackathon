"""Stage 1b: Inspect anomalous raw values to define cleaning rules."""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "dataset_start"

pdly = pd.read_csv(DATA / "01_market_prices_raw.csv", encoding="utf-8-sig")
pintra = pd.read_csv(DATA / "01_market_prices_raw_expanded.csv", encoding="utf-8-sig")
fund = pd.read_csv(DATA / "03_fundamentals_raw.csv", encoding="utf-8-sig")

print("### volume anomalies (daily) ###")
vol_num = pd.to_numeric(pdly.volume, errors="coerce")
bad = pdly[vol_num.isna() & pdly.volume.notna()]
print(bad[["date", "asset_id", "volume"]].to_string())
print("rows with NA volume:", pdly.volume.isna().sum())

print("\n### volume anomalies (intraday) ###")
vol_num_i = pd.to_numeric(pintra.volume, errors="coerce")
badi = pintra[vol_num_i.isna() & pintra.volume.notna()]
print(badi[["date", "asset_id", "volume"]].head(20).to_string())
print("rows with NA volume:", pintra.volume.isna().sum())

print("\n### revenue anomalies (fundamentals) ###")
rev_num = pd.to_numeric(fund.revenue_usd_m, errors="coerce")
badr = fund[rev_num.isna() & fund.revenue_usd_m.notna()]
print(badr.to_string())

print("\n### unparseable dates (daily) ###")
d = pd.to_datetime(pdly.date, errors="coerce", format="mixed")
print(pdly[d.isna()][["date", "asset_id"]].to_string())

print("\n### date format variants (daily) ###")
slash = pdly[pdly.date.str.contains("/", na=False)]
print(f"rows with MM/DD/YYYY format: {len(slash)}")
print(slash[["date", "asset_id"]].head(10).to_string())

print("\n### unparseable dates (intraday) ###")
di = pd.to_datetime(pintra.date, errors="coerce", format="mixed")
print(pintra[di.isna()][["date", "asset_id"]].head(40).to_string())

print("\n### unparseable period_end (fundamentals) ###")
dp = pd.to_datetime(fund.period_end, errors="coerce", format="mixed")
print(fund[dp.isna()].to_string())

print("\n### duplicated rows (daily) ###")
print(pdly[pdly.duplicated(keep=False)].sort_values(["asset_id", "date"]).to_string())

print("\n### currency missing rows (daily) ###")
print(pdly[pdly.currency.isna()][["date", "asset_id", "market", "currency"]].to_string())

print("\n### dirty asset_id rows (daily) ###")
print(pdly[pdly.asset_id.isin(["VF-A1", "VFA03", "VF_A6"])].to_string())

print("\n### OHLC sanity: high<low or negative prices (daily) ###")
bad_ohlc = pdly[(pdly.high < pdly.low) | (pdly.close <= 0) | (pdly.open <= 0)]
print(f"count: {len(bad_ohlc)}")
print(bad_ohlc.head(10).to_string())

print("\n### close missing (intraday) ###")
print(pintra[pintra.close.isna()][["date", "asset_id", "open", "high", "low", "close"]].head(30).to_string())

print("\n### intraday dirty asset ids ###")
print(pintra[pintra.asset_id.isin(["VF-A1", "VF-A4", "VF-A6"])].groupby("asset_id").size())

print("\n### fundamentals duplicates ###")
print(fund[fund.duplicated(keep=False)].to_string())

print("\n### fundamentals ISS04 rows ###")
print(fund[fund.issuer_id == "ISS04"].to_string())
