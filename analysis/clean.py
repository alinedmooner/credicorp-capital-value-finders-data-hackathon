"""Shared cleaning layer.

Fixes all data-quality issues found in stage 1:
- malformed asset_id / issuer_id variants (VF-A1, VFA03, VF_A6, VF-A4, VF-A6, ISS04)
- mixed date formats (ISO + MM/DD/YYYY) and 'Q4-2024' period labels
- numeric fields stored as text with 'K' suffix (volume) or thousands separator (revenue)
- exact duplicate rows
- missing currency (all assets are USD) and missing close in intraday
"""
import re
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "dataset_start"

ASSET_ID_MAP = {
    "VF-A1": "VF_A01", "VFA03": "VF_A03", "VF_A6": "VF_A06",
    "VF-A4": "VF_A04", "VF-A6": "VF_A06",
}
ISSUER_ID_MAP = {"ISS04": "ISS_04"}


def _parse_num(s: pd.Series) -> pd.Series:
    """Parse numbers that may contain 'K' suffix or thousands separators."""
    def conv(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, float)):
            return float(x)
        x = str(x).strip().replace(",", "")
        m = re.fullmatch(r"(-?\d+(?:\.\d+)?)([KkMm])", x)
        if m:
            mult = 1_000 if m.group(2).lower() == "k" else 1_000_000
            return float(m.group(1)) * mult
        try:
            return float(x)
        except ValueError:
            return np.nan
    return s.map(conv)


def _parse_date_mixed(s: pd.Series) -> pd.Series:
    """Parse ISO dates, MM/DD/YYYY dates, and 'Qn-YYYY' quarter labels."""
    def conv(x):
        if pd.isna(x):
            return pd.NaT
        x = str(x).strip()
        m = re.fullmatch(r"Q([1-4])-(\d{4})", x)
        if m:
            q, y = int(m.group(1)), int(m.group(2))
            return pd.Timestamp(y, q * 3, 1) + pd.offsets.MonthEnd(0)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return pd.to_datetime(x, format=fmt)
            except ValueError:
                continue
        return pd.NaT
    return s.map(conv)


def _repair_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """Replace OHLC values lying outside the [low, high] band with NaN and
    interpolate per asset (e.g. VF_A06 2026-03-23 close=3589 vs high=35.92)."""
    df = df.copy()
    for col in ("open", "close"):
        bad = (df[col] > df["high"]) | (df[col] < df["low"])
        df.loc[bad, col] = np.nan
    for col in ("open", "close"):
        df[col] = df.groupby("asset_id")[col].transform(
            lambda s: s.interpolate(limit_direction="both"))
    return df


def load_prices_daily() -> pd.DataFrame:
    df = pd.read_csv(DATA / "01_market_prices_raw.csv", encoding="utf-8-sig")
    df["asset_id"] = df["asset_id"].replace(ASSET_ID_MAP)
    df["date"] = _parse_date_mixed(df["date"])
    df["volume"] = _parse_num(df["volume"])
    df["currency"] = df["currency"].fillna("USD")
    df = df.drop_duplicates()
    df = df.dropna(subset=["date"])
    df = df.sort_values(["asset_id", "date"]).reset_index(drop=True)
    df = _repair_ohlc(df)
    return df


def load_prices_intraday() -> pd.DataFrame:
    df = pd.read_csv(DATA / "01_market_prices_raw_expanded.csv", encoding="utf-8-sig")
    df["asset_id"] = df["asset_id"].replace(ASSET_ID_MAP)
    df["date"] = _parse_date_mixed(df["date"])
    df["volume"] = _parse_num(df["volume"])
    df["currency"] = df["currency"].fillna("USD")
    df = df.drop_duplicates()
    df = df.dropna(subset=["date"])
    # missing close: fill with midpoint of high/low when available, else open
    mid = (df["high"] + df["low"]) / 2
    df["close"] = df["close"].fillna(mid).fillna(df["open"])
    df = df.sort_values(["asset_id", "date"]).reset_index(drop=True)
    df = _repair_ohlc(df)
    return df


def load_macro() -> pd.DataFrame:
    df = pd.read_csv(DATA / "02_macro_raw.csv", encoding="utf-8-sig")
    df["date"] = _parse_date_mixed(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # inflation is a monthly series on a daily grid -> forward fill
    df["us_inflation_yoy"] = df["us_inflation_yoy"].ffill()
    return df


def load_fundamentals() -> pd.DataFrame:
    df = pd.read_csv(DATA / "03_fundamentals_raw.csv", encoding="utf-8-sig")
    df["issuer_id"] = df["issuer_id"].replace(ISSUER_ID_MAP)
    df["period_end"] = _parse_date_mixed(df["period_end"])
    df["revenue_usd_m"] = _parse_num(df["revenue_usd_m"])
    df = df.drop_duplicates()
    # ISS_02 has both '2024-12-31' and 'Q4-2024' rows with different values;
    # keep the explicitly-dated row (appears first in the file)
    df = df.drop_duplicates(subset=["issuer_id", "period_end"], keep="first")
    df = df.sort_values(["issuer_id", "period_end"]).reset_index(drop=True)
    return df


def load_assets() -> pd.DataFrame:
    return pd.read_csv(DATA / "04_asset_reference.csv", encoding="utf-8-sig")


def load_clients() -> pd.DataFrame:
    return pd.read_csv(DATA / "05_client_profiles.csv", encoding="utf-8-sig")


def load_events() -> pd.DataFrame:
    df = pd.read_csv(DATA / "06_events.csv", encoding="utf-8-sig")
    df["event_date"] = _parse_date_mixed(df["event_date"])
    return df


if __name__ == "__main__":
    for name, loader in [("daily", load_prices_daily), ("intraday", load_prices_intraday),
                         ("macro", load_macro), ("fundamentals", load_fundamentals)]:
        df = loader()
        print(f"{name}: {df.shape}, nulls={int(df.isna().sum().sum())}")
        if "asset_id" in df:
            print("  asset_ids:", sorted(df.asset_id.unique()))
        if "issuer_id" in df:
            print("  issuer_ids:", sorted(df.issuer_id.unique()))
