"""
Backfills missing daily reports with data-only fallback reports.

Each report only uses data dated strictly before the report date, mirroring what the
06:00 KST pipeline run would have seen. Existing reports (DB or file) are never overwritten.

Usage: python backfill_fallback_reports.py 2026-09-11 2026-09-23 [--reason "..."] [--dry-run] [--ai]
  --ai replaces data-only fallback reports with Gemini analysis of that date's market data.
"""
import argparse
import os
from datetime import date, timedelta
from typing import Any, Dict

import pandas as pd

from app.config import AppConfig
from app.data_fetcher import AssetDataFetcher
from app.database import get_daily_report_by_date, save_daily_report
from app.fallback_report import build_fallback_report, price_table_lines
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


FALLBACK_TITLE_MARKER = "(AI 분석 미생성)"


def backfill_instructions(ds: str, market: Dict[str, Any]) -> str:
    return "\n".join([
        f"- 이 보고서는 **{ds} 06:00 KST 시점**을 기준으로 사후에 재구성한 보고서입니다. 보고서 제목과 발행일자는 반드시 {ds}로 표기하세요 (오늘 날짜를 쓰지 마세요).",
        f"- 제목 바로 아래에 다음 문구를 그대로 넣으세요: `> ℹ️ 사후 재구성 리포트: 당일 뉴스·유튜브 데이터 없이 {ds} 시점 시장 데이터만으로 작성되었습니다.`",
        "- 해당 날짜의 뉴스와 유튜브 영상 데이터는 없습니다. '개별 전문가 영상 요약' 섹션은 '해당일 수집 데이터 없음'으로 한 줄만 표기하고, 존재하지 않는 영상·뉴스·전문가 의견을 절대 지어내지 마세요.",
        f"- {ds} 이후에 일어난 사건이나 가격은 언급하지 마세요. 아래 가격표와 위의 거시 데이터만 근거로 분석하세요.",
        "",
        "#### 관심종목 및 주요 자산 가격 (전일 종가 기준)",
        *price_table_lines(market),
    ])


def backfill_with_ai(market: Dict[str, Any], start: date, end: date, dry_run: bool) -> None:
    """Replaces missing or data-only fallback reports with Gemini analysis of that date's market data."""
    from app.portfolio_manager import PortfolioManager
    from app.recommender import RecommendationEngine
    from app.report_indexer import index_report

    try:
        model = PortfolioManager(AppConfig.PORTFOLIO_FILE_PATH).load_portfolio().get("gemini_model", "gemini-3.5-flash")
    except Exception:
        model = "gemini-3.5-flash"
    engine = RecommendationEngine(AppConfig.GEMINI_API_KEY, model_name=model)
    print(f"Using Gemini model: {model}")

    replaced, skipped, failed = [], [], []
    d = start
    while d <= end:
        ds = d.isoformat()
        existing = get_daily_report_by_date(ds)
        if existing and FALLBACK_TITLE_MARKER not in (existing.get("title") or ""):
            skipped.append(ds)  # already a real AI report — never overwrite
        elif dry_run:
            replaced.append(ds)
        else:
            day_market = market_as_of(market, d)
            try:
                md = engine.generate_recommendation_report(
                    market=day_market, news=[], youtube=[], extra_instructions=backfill_instructions(ds, day_market)
                )
            except Exception as e:
                logger.error(f"AI backfill failed for {ds}, keeping existing report: {e}")
                failed.append(ds)
                d += timedelta(days=1)
                continue
            path = f"reports/{ds}_report.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            if not index_report(md, ds, file_path=path):
                raise SystemExit(f"DB indexing failed for {ds}")
            print(f"{ds}: replaced -> {md.splitlines()[0][:80]}", flush=True)
            replaced.append(ds)
        d += timedelta(days=1)

    print(f"{'would replace' if dry_run else 'replaced'} ({len(replaced)}): {replaced}")
    print(f"skipped real AI reports ({len(skipped)}): {skipped}")
    print(f"failed ({len(failed)}): {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("start")
    parser.add_argument("end")
    parser.add_argument("--reason", default="Gemini API 월 지출 한도 초과(429 spending cap)로 당일 AI 분석 미생성 — 사후 데이터 백필")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without writing")
    parser.add_argument("--ai", action="store_true",
                        help="Generate Gemini analysis from each date's market data, replacing data-only fallback reports")
    args = parser.parse_args()

    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    market = fetch_market_data()
    os.makedirs("reports", exist_ok=True)

    if args.ai:
        backfill_with_ai(market, start, end, args.dry_run)
        return

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
