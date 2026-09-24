"""
Data-only daily report used when the Gemini report generation fails (quota, spending cap, outage).
Keeps the web archive populated with raw market data instead of leaving a gap.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


def _last_and_change(df: Optional[pd.DataFrame], column: str):
    """Returns (last value, % change vs previous row) or (None, None)."""
    if df is None or df.empty or column not in df.columns:
        return None, None
    series = df[column].dropna()
    if series.empty:
        return None, None
    last = float(series.iloc[-1])
    if len(series) < 2 or float(series.iloc[-2]) == 0:
        return last, None
    prev = float(series.iloc[-2])
    return last, (last - prev) / prev * 100


def _fmt(value: Optional[float], digits: int = 2) -> str:
    return "-" if value is None else f"{value:,.{digits}f}"


def _fmt_pct(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:+.2f}%"


def build_fallback_report(
    market: Dict[str, Any],
    news: List[Dict[str, Any]],
    failure_reason: str,
    report_date: Optional[str] = None
) -> str:
    report_date = report_date or datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# {report_date} 일일 시장 데이터 리포트 (AI 분석 미생성)",
        "",
        "> ⚠️ **AI 분석 리포트 생성 실패** — Gemini 호출이 실패하여 수집된 시장 데이터만으로 작성된 대체 리포트입니다.",
        f"> 실패 사유: `{failure_reason[:200]}`",
        "",
        "### 1. 요약",
        "AI 분석이 생성되지 않아 투자 추천 및 리밸런싱 제안은 포함되지 않습니다. 아래는 당일 수집된 원천 데이터입니다.",
        "",
        "---",
        "",
        "### 2. 주요 종목 및 자산 가격",
        "",
        "| 티커 | 종가 | 전일 대비 |",
        "| :--- | ---: | ---: |",
    ]
    for ticker, df in (market.get("prices") or {}).items():
        last, chg = _last_and_change(df, "Close")
        lines.append(f"| {ticker} | {_fmt(last)} | {_fmt_pct(chg)} |")

    for key, df in (market.get("exchange_rates") or {}).items():
        last, chg = _last_and_change(df, "Close")
        lines.append(f"| {key} | {_fmt(last)} | {_fmt_pct(chg)} |")

    yields = market.get("yields") or {}
    if yields:
        lines += ["", "### 3. 채권 금리", "", "| 지표 | 금리(%) | 전일 대비 |", "| :--- | ---: | ---: |"]
        for key, df in yields.items():
            last, chg = _last_and_change(df, "Yield")
            lines.append(f"| {key} | {_fmt(last, 3)} | {_fmt_pct(chg)} |")

    macro = market.get("macro") or {}
    if macro:
        lines += ["", "### 4. 거시경제 지표 (FRED)", "", "| 지표 | 최신값 |", "| :--- | ---: |"]
        for key, df in macro.items():
            last, _ = _last_and_change(df, "Value")
            lines.append(f"| {key} | {_fmt(last)} |")

    if news:
        lines += ["", "### 5. 주요 뉴스 헤드라인", ""]
        for item in news[:15]:
            title = item.get("title", "").replace("\n", " ")
            source = item.get("source", "")
            link = item.get("link", "")
            suffix = f" — {source}" if source else ""
            lines.append(f"- [{title}]({link}){suffix}" if link else f"- {title}{suffix}")

    lines += ["", "---", "", "*이 리포트는 AI 분석 실패 시 자동 생성되는 데이터 요약본입니다. Gemini 한도/키 상태를 확인하세요.*", ""]
    return "\n".join(lines)
