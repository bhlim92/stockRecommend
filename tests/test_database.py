import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, ScreenerResult, save_screener_results

@pytest.fixture
def temp_db():
    # setup in-memory sqlite engine for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Patch SessionLocal inside app.database to use this in-memory test DB session
    with patch("app.database.SessionLocal", TestingSessionLocal):
        yield TestingSessionLocal
        
    Base.metadata.drop_all(bind=engine)

def test_save_screener_results_success(temp_db):
    results = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": 180.5,
            "entry_score": 85,
            "eval_score": 90,
            "total_score": 175,
            "rationale": "Perfect trend"
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corp.",
            "current_price": None, # Should support None
            "entry_score": None,   # Should filter out if total_score is None, but let's test with total_score defined
            "eval_score": 80,
            "total_score": 140,
            "rationale": "Steady growth"
        },
        {
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "current_price": None,
            "entry_score": None,
            "eval_score": None,
            "total_score": None, # This should be filtered out (skipped)
            "rationale": "Pending analysis"
        }
    ]
    
    success = save_screener_results("sp500", results)
    assert success is True
    
    # Query database and verify
    db = temp_db()
    records = db.query(ScreenerResult).all()
    assert len(records) == 2 # TSLA should have been filtered out because total_score is None
    
    # Check AAPL
    aapl_rec = db.query(ScreenerResult).filter(ScreenerResult.symbol == "AAPL").first()
    assert aapl_rec is not None
    assert aapl_rec.market == "sp500"
    assert aapl_rec.name == "Apple Inc."
    assert aapl_rec.current_price == 180.5
    assert aapl_rec.entry_score == 85
    assert aapl_rec.eval_score == 90
    assert aapl_rec.total_score == 175
    assert aapl_rec.rationale == "Perfect trend"
    assert aapl_rec.created_at is not None
    
    # Check MSFT
    msft_rec = db.query(ScreenerResult).filter(ScreenerResult.symbol == "MSFT").first()
    assert msft_rec is not None
    assert msft_rec.current_price is None
    assert msft_rec.total_score == 140
    
    # Both AAPL and MSFT should share the exact same fallback timestamp
    assert aapl_rec.created_at == msft_rec.created_at
    
    # TSLA should not exist
    tsla_rec = db.query(ScreenerResult).filter(ScreenerResult.symbol == "TSLA").first()
    assert tsla_rec is None
    
    db.close()

def test_save_screener_results_with_provided_timestamp(temp_db):
    results = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "total_score": 175,
            "created_at": "2026-06-03 10:00:00"
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corp.",
            "total_score": 140,
            "created_at": "2026-06-03 10:00:00"
        }
    ]
    
    success = save_screener_results("sp500", results)
    assert success is True
    
    db = temp_db()
    aapl_rec = db.query(ScreenerResult).filter(ScreenerResult.symbol == "AAPL").first()
    msft_rec = db.query(ScreenerResult).filter(ScreenerResult.symbol == "MSFT").first()
    
    assert aapl_rec is not None
    assert msft_rec is not None
    
    # Both records must share the exact same parsed datetime from the input
    assert aapl_rec.created_at == msft_rec.created_at
    assert aapl_rec.created_at.strftime("%Y-%m-%d %H:%M:%S") == "2026-06-03 10:00:00"
    
    db.close()

def test_daily_report_save_and_search(temp_db):
    from app.database import save_daily_report, search_daily_reports, get_daily_report_by_date, list_daily_report_dates
    
    # 1. Save Report
    rec_stocks = [
        {"symbol": "005930.KS", "name": "Samsung Electronics", "action": "BUY", "sector": "Semiconductor"},
        {"symbol": "AAPL", "name": "Apple Inc.", "action": "HOLD", "sector": "Tech"}
    ]
    reb_actions = [
        {"asset_class": "Equities", "action": "BUY", "amount": 1000}
    ]
    
    success = save_daily_report(
        report_date="2026-08-23",
        title="2026-08-23 Daily Stock Recommendation Report",
        macro_summary="환율 1380원 안정화 및 반도체 섹터 강세",
        content="# 2026-08-23 Report\n금리 인하 기대로 인하여 삼성전자(005930.KS) 매수 권고.",
        recommended_stocks=rec_stocks,
        rebalance_actions=reb_actions,
        file_path="reports/2026-08-23_report.md",
        gdrive_link="https://docs.google.com/test_doc"
    )
    assert success is True
    
    # 2. Search by keyword
    search_res = search_daily_reports(q="반도체")
    assert search_res["total"] >= 1
    assert search_res["results"][0]["report_date"] == "2026-08-23"
    assert search_res["results"][0]["title"] == "2026-08-23 Daily Stock Recommendation Report"
    
    # 3. Search by symbol
    sym_res = search_daily_reports(symbol="005930.KS")
    assert sym_res["total"] == 1
    
    # 4. Get Detail
    detail = get_daily_report_by_date("2026-08-23")
    assert detail is not None
    assert detail["title"] == "2026-08-23 Daily Stock Recommendation Report"
    assert len(detail["recommended_stocks"]) == 2
    assert detail["gdrive_link"] == "https://docs.google.com/test_doc"
    
    # 5. List Dates
    dates = list_daily_report_dates()
    assert len(dates) >= 1
    assert dates[0]["report_date"] == "2026-08-23"

