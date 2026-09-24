import re

import pandas as pd

from app.fallback_report import build_fallback_report


def test_fallback_report_contains_market_data_and_reason():
    market = {
        "prices": {"AAPL": pd.DataFrame({"Close": [100.0, 110.0]}), "EMPTY": pd.DataFrame()},
        "yields": {"US10Y": pd.DataFrame({"Yield": [4.0, 4.1]})},
        "macro": {"CPI": pd.DataFrame({"Value": [310.5]})},
        "exchange_rates": {"USD_KRW": pd.DataFrame({"Close": [1380.0, 1390.0]})},
    }
    news = [{"title": "Fed holds rates", "link": "https://example.com/a", "source": "Reuters"}]

    md = build_fallback_report(market, news, "429 spending cap exceeded", report_date="2026-09-24")

    assert md.startswith("# 2026-09-24 일일 시장 데이터 리포트")
    assert "429 spending cap exceeded" in md
    assert "| AAPL | 110.00 | +10.00% |" in md
    assert "| EMPTY | - | - |" in md
    assert "| US10Y | 4.100 | +2.50% |" in md
    assert "| CPI | 310.50 |" in md
    assert "[Fed holds rates](https://example.com/a) — Reuters" in md
    # main.py's recommended-stock parser only matches bold first cells; data rows must not become BUY tags
    assert re.findall(r'\|\s*\*\*?([^\*\|]+)\*\*?\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|', md) == []


def test_fallback_report_handles_empty_market():
    md = build_fallback_report({}, [], "boom", report_date="2026-09-24")
    assert "AI 분석 리포트 생성 실패" in md
