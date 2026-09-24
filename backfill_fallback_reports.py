"""
Backfills missing daily reports with data-only fallback reports.

Each report only uses data dated strictly before the report date, mirroring what the
06:00 KST pipeline run would have seen. Existing reports (DB or file) are never overwritten.

Usage: python backfill_fallback_reports.py 2026-09-11 2026-09-23 [--reason "..."] [--dry-run]
"""
import argparse
import os
from datetime import date, timedelta
from typing import Any, Dict

import pandas as pd

from app.config import AppConfig
from app.data_fetcher import AssetDataFetcher
from app.database import get_daily_report_by_date, save_daily_report
from app.fallback_report import build_fallback_report
from app.utils.helpers import get_date_n_days_ago
from app.utils.logger import setup_logger

logger = setup_logger("backfill", AppConfig.LOG_FILE_PATH, AppConfig.LOG_LEVEL)


def fetch_market_data() -> Dict[str, Any]:
    """Same ingestion as main.py, fetched once and sliced per date."""
    us = os.getenv("US_WATCHLIST")
    kr = os.getenv("KR_WATCHLIST")
    watchlist = ([t.strip() for t in us.split(",")] if us else AppConfig.US_WATCHLIST) + \
                ([t.strip() for t in kr.split(",")] if kr else AppConfig.KR_WATCHLIST)

    fetcher = AssetDataFetcher()
    market: Dict[str, Any] = {"prices": {}, "yields": {}, "macro": {}, "exchange_rates": {}}
    for ticker in watchlist:
        try:
            market["prices"][ticker] = fetcher.fetch_historical_prices(ticker, period="1y", interval="1d")
        except Exception as e:
            logger.warning(f"Price history unavailable for {ticker}: {e}")

    for key, ticker in AppConfig.MACRO_TICKERS.items():
        try:
            if key in ["US10Y", "US30Y", "KR10YT=RR"] or "10Y" in key or "30Y" in key:
                market["yields"][key] = fetcher.fetch_bond_yield(ticker, period="1y")
            elif key == "USD_KRW" or ticker == "USDKRW=X":
                market["exchange_rates"]["USD_KRW"] = fetcher.fetch_historical_prices(ticker, period="1y")
            else:
                market["prices"][key] = fetcher.fetch_historical_prices(ticker, period="1y")
        except Exception as e:
            logger.warning(f"Macro data unavailable for {key} ({ticker}): {e}")

    start = get_date_n_days_ago(365 * 3)
    for key, indicator_id in AppConfig.FRED_INDICATORS.items():
        try:
            market["macro"][key] = fetcher.fetch_fred_indicator(indicator_id, start_date=start)
        except Exception as e:
            logger.warning(f"FRED indicator unavailable for {key}: {e}")
    return market


def slice_before(df: pd.DataFrame, cutoff: date) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    idx = pd.to_datetime(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    return df[idx.normalize() < pd.Timestamp(cutoff)]


def market_as_of(market: Dict[str, Any], cutoff: date) -> Dict[str, Any]:
    return {group: {k: slice_before(df, cutoff) for k, df in items.items()} for group, items in market.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("start")
    parser.add_argument("end")
    parser.add_argument("--reason", default="Gemini API 월 지출 한도 초과(429 spending cap)로 당일 AI 분석 미생성 — 사후 데이터 백필")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without writing")
    args = parser.parse_args()

    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    market = fetch_market_data()
    os.makedirs("reports", exist_ok=True)

    created, skipped = [], []
    d = start
    while d <= end:
        ds = d.isoformat()
        path = f"reports/{ds}_report.md"
        if get_daily_report_by_date(ds) or os.path.exists(path):
            skipped.append(ds)
        else:
            md = build_fallback_report(market_as_of(market, d), [], args.reason, report_date=ds)
            if args.dry_run:
                print(f"--- {ds} (dry-run) ---\n{md[:600]}\n")
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(md)
                ok = save_daily_report(
                    report_date=ds,
                    title=md.splitlines()[0].lstrip("# ").strip(),
                    macro_summary="AI 분석이 생성되지 않아 시장 데이터만 수록된 대체 리포트입니다.",
                    content=md,
                    recommended_stocks=[],
                    file_path=path,
                )
                if not ok:
                    raise SystemExit(f"DB indexing failed for {ds}")
            created.append(ds)
        d += timedelta(days=1)

    print(f"created ({len(created)}): {created}")
    print(f"skipped existing ({len(skipped)}): {skipped}")


if __name__ == "__main__":
    main()
