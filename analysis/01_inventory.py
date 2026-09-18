"""Stage 1: Inventory & data-quality audit of all datasets."""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "dataset_start"
OUT = Path(__file__).resolve().parent

FILES = {
    "prices_daily": "01_market_prices_raw.csv",
    "prices_intraday": "01_market_prices_raw_expanded.csv",
    "macro": "02_macro_raw.csv",
    "fundamentals": "03_fundamentals_raw.csv",
    "assets": "04_asset_reference.csv",
    "clients": "05_client_profiles.csv",
    "events": "06_events.csv",
}

report = []

def log(msg=""):
    print(msg)
    report.append(msg)

for key, fname in FILES.items():
    path = DATA / fname
    # utf-8-sig handles the BOM present in several files
    df = pd.read_csv(path, encoding="utf-8-sig")
    log("=" * 78)
    log(f"FILE: {fname}  (key: {key})")
    log(f"  shape: {df.shape[0]:,} rows x {df.shape[1]} cols")
    log(f"  columns: {list(df.columns)}")
    log(f"  dtypes:")
    for c in df.columns:
        log(f"    - {c}: {df[c].dtype}")
    # missing values
    miss = df.isna().sum()
    miss = miss[miss > 0]
    if len(miss):
        log(f"  MISSING VALUES:")
        for c, n in miss.items():
            log(f"    - {c}: {n:,} ({n/len(df)*100:.1f}%)")
    else:
        log(f"  missing values: none")
    # duplicates
    ndup = df.duplicated().sum()
    log(f"  full-row duplicates: {ndup:,}")
    # date ranges
    for dc in ("date", "period_end", "event_date"):
        if dc in df.columns:
            d = pd.to_datetime(df[dc], errors="coerce")
            nat = d.isna().sum()
            log(f"  date col '{dc}': min={d.min()}, max={d.max()}, unparseable={nat}")
    # key cardinality
    for kc in ("asset_id", "issuer_id", "client_id", "market", "sector",
               "country", "currency", "risk_regime", "event_type", "severity", "scope"):
        if kc in df.columns:
            log(f"  unique {kc}: {df[kc].nunique()} -> {sorted(df[kc].dropna().unique().tolist())[:15]}")
    log()

# entity-relationship consistency checks
log("=" * 78)
log("REFERENTIAL INTEGRITY")
assets = pd.read_csv(DATA / FILES["assets"], encoding="utf-8-sig")
fund = pd.read_csv(DATA / FILES["fundamentals"], encoding="utf-8-sig")
pdly = pd.read_csv(DATA / FILES["prices_daily"], encoding="utf-8-sig")
pintra = pd.read_csv(DATA / FILES["prices_intraday"], encoding="utf-8-sig")
ev = pd.read_csv(DATA / FILES["events"], encoding="utf-8-sig")

a_ids = set(assets.asset_id)
log(f"asset_ids in reference: {sorted(a_ids)}")
log(f"asset_ids in daily prices not in reference: {sorted(set(pdly.asset_id) - a_ids)}")
log(f"asset_ids in intraday prices not in reference: {sorted(set(pintra.asset_id) - a_ids)}")
i_ids = set(assets.issuer_id)
log(f"issuer_ids in reference: {sorted(i_ids)}")
log(f"issuer_ids in fundamentals not in reference: {sorted(set(fund.issuer_id) - i_ids)}")
log(f"issuers in reference without fundamentals: {sorted(i_ids - set(fund.issuer_id))}")
ev_scopes = set(ev.scope)
log(f"event scopes: {sorted(ev_scopes)}; scopes not matching asset_ids: {sorted(ev_scopes - a_ids)}")

# per-asset daily coverage
log()
log("DAILY PRICE COVERAGE PER ASSET:")
cov = pdly.groupby("asset_id").agg(
    n=("date", "count"),
    first=("date", "min"),
    last=("date", "max"),
)
log(cov.to_string())

(OUT / "01_inventory_report.txt").write_text("\n".join(report), encoding="utf-8")
print("\nSaved -> analysis/01_inventory_report.txt")
