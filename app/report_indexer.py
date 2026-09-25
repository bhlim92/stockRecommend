"""
Indexes a generated report markdown into the daily_reports table.
Shared by the scheduled pipeline (main.py) and the on-demand web pipeline, so both show up in the web archive.
"""
import re
from typing import Any, Dict, List, Optional

from app.database import save_daily_report


def parse_report(report_markdown: str, report_date: str) -> Dict[str, Any]:
    """Extracts title, macro summary and recommended-stock tags from report markdown."""
    title_match = re.search(r'^#\s+(.+)$', report_markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"{report_date} Daily Investment Report"

    macro_match = re.search(r'###\s+1\.\s+요약[^\n]*\n(.*?)(?=\n---|\n###|\Z)', report_markdown, re.DOTALL)
    macro_summary = macro_match.group(1).strip() if macro_match else ""
    if not macro_summary:
        paras = [p.strip() for p in report_markdown.split("\n\n") if p.strip() and not p.startswith("#")]
        macro_summary = paras[0] if paras else ""

    recommended_stocks: List[Dict[str, str]] = []
    table_rows = re.findall(r'\|\s*\*\*?([^\*\|]+)\*\*?\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|', report_markdown)
    for row in table_rows:
        col1, col2, col3 = row[0].strip(), row[1].strip(), row[2].strip()
        if "섹터" in col1 or "종목" in col1 or "---" in col1:
            continue
        action = "BUY"
        if "매도" in report_markdown and (col1 in report_markdown.split("매도")[1] or col2 in report_markdown.split("매도")[1]):
            action = "SELL"
        recommended_stocks.append({"sector": col1, "symbol": col2, "reason": col3, "action": action})

    return {"title": title, "macro_summary": macro_summary, "recommended_stocks": recommended_stocks}


def index_report(report_markdown: str, report_date: str, file_path: Optional[str] = None, gdrive_link: Optional[str] = None) -> bool:
    """Parses and saves (upserts) the report for report_date. Returns False on failure."""
    parsed = parse_report(report_markdown, report_date)
    return save_daily_report(
        report_date=report_date,
        title=parsed["title"],
        macro_summary=parsed["macro_summary"],
        content=report_markdown,
        recommended_stocks=parsed["recommended_stocks"],
        file_path=file_path,
        gdrive_link=gdrive_link,
    )
