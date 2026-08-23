import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Setup database logger
logger = logging.getLogger("database")

Base = declarative_base()

class ScreenerResult(Base):
    __tablename__ = 'screener_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    market = Column(String(20), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    current_price = Column(Float, nullable=True)
    entry_score = Column(Integer, nullable=True)
    eval_score = Column(Integer, nullable=True)
    total_score = Column(Integer, nullable=True)
    rationale = Column(Text, nullable=True)
    sector = Column(String(100), nullable=True)
    analyst_rating = Column(String(20), nullable=True)      # 한국어 라벨 (예: 강력매수)
    analyst_rating_raw = Column(String(30), nullable=True)  # yfinance raw key (예: strong_buy)
    analyst_count = Column(Integer, nullable=True)           # 애널리스트 수
    trend_pct = Column(Float, nullable=True)                 # 20일 등락률(%)
    sparkline_prices = Column(Text, nullable=True)           # JSON 배열 문자열
    sparkline_volumes = Column(Text, nullable=True)          # JSON 배열 문자열
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Database Engine initialization
engine = None
SessionLocal = None

def get_db_url() -> str:
    db_type = os.getenv("DB_TYPE", "").lower()
    # Fallback to sqlite if DB_TYPE is not set or empty
    if not db_type:
        if os.getenv("TESTING", "").lower() == "true":
            return ""
        db_type = "sqlite"
    
    db_name = os.getenv("DB_NAME", "")
    
    if db_type == "sqlite":
        db_file = db_name if db_name else "stock_db.sqlite"
        # If relative filename (no directories), put it in the project's data directory
        if not os.path.isabs(db_file) and "/" not in db_file and "\\" not in db_file:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(root_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_file = os.path.join(data_dir, db_file)
        abs_path = os.path.abspath(db_file).replace("\\", "/")
        return f"sqlite:///{abs_path}"
    
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306" if db_type == "mariadb" else "5432")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    
    if not user or not db_name:
        logger.warning("Database configuration missing username or database name. DB integration disabled.")
        return ""
        
    if db_type == "mariadb" or db_type == "mysql":
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"
    elif db_type == "postgresql":
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    logger.warning(f"Unsupported database type: {db_type}. DB integration disabled.")
    return ""

def init_db():
    global engine, SessionLocal
    db_url = get_db_url()
    if not db_url:
        return False
        
    try:
        # Prevent PyMySQL encoding issues with MariaDB by using safe parameters
        if "mysql+pymysql" in db_url:
            engine = create_engine(db_url, pool_recycle=3600, pool_pre_ping=True)
        else:
            engine = create_engine(db_url, pool_pre_ping=True)
            
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # ─── 자동 컬럼 마이그레이션 ───────────────────────────────────────
        # create_all은 기존 테이블에 새 컬럼을 추가하지 않으므로
        # 누락된 컬럼을 감지해 ALTER TABLE로 자동 추가합니다.
        _migrate_add_missing_columns(engine)
        # ──────────────────────────────────────────────────────────────────
        
        logger.info("Database successfully connected and tables verified.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        engine = None
        SessionLocal = None
        return False


def _migrate_add_missing_columns(eng):
    """screener_results 테이블에 신규 컬럼이 없으면 ALTER TABLE로 추가합니다."""
    # 추가해야 할 컬럼: (name, ddl_fragment)
    new_columns = [
        ("sector",              "VARCHAR(100)"),
        ("analyst_rating",      "VARCHAR(20)"),
        ("analyst_rating_raw",  "VARCHAR(30)"),
        ("analyst_count",       "INT"),
        ("trend_pct",           "FLOAT"),
        ("sparkline_prices",    "TEXT"),
        ("sparkline_volumes",   "TEXT"),
    ]
    try:
        with eng.connect() as conn:
            # 현재 컬럼 목록 조회 (DB 종류에 관계없이 동작)
            result = conn.execute(
                __import__("sqlalchemy").text("SELECT * FROM screener_results LIMIT 0")
            )
            existing_cols = {col.lower() for col in result.keys()}
            
            for col_name, col_type in new_columns:
                if col_name.lower() not in existing_cols:
                    try:
                        conn.execute(__import__("sqlalchemy").text(
                            f"ALTER TABLE screener_results ADD COLUMN {col_name} {col_type}"
                        ))
                        # SQLite는 autocommit, MariaDB는 명시적 commit 필요
                        try:
                            conn.commit()
                        except Exception:
                            pass
                        logger.info(f"Migration: added column '{col_name}' to screener_results.")
                    except Exception as col_err:
                        # 이미 존재하거나 지원하지 않는 경우 무시
                        logger.debug(f"Migration skip '{col_name}': {col_err}")
    except Exception as e:
        logger.warning(f"Migration check failed (non-critical): {e}")

# Trigger initialization on module import
init_db()

def save_screener_results(market: str, results: List[Dict[str, Any]]) -> bool:
    """Saves all non-empty results to the configured RDBMS in a bulk insert."""
    global SessionLocal
    if SessionLocal is None:
        # Try to reinitialize in case configuration changed at runtime
        if not init_db():
            return False
            
    try:
        db = SessionLocal()
        db_records = []
        
        # Find the scan start time from the results to ensure all records share the exact same timestamp
        scan_time = None
        for item in results:
            if item.get("created_at") and item["created_at"] != "-":
                try:
                    scan_time = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
                    break
                except Exception:
                    pass
                    
        if not scan_time:
            scan_time = datetime.utcnow()
        
        import json
        for item in results:
            # Only save items that have been actually analyzed (score not None)
            if item.get("total_score") is not None:
                # sparkline 데이터를 JSON 문자열로 직렬화
                sp = item.get("sparkline_prices")
                sv = item.get("sparkline_volumes")
                sp_json = json.dumps(sp) if isinstance(sp, list) else None
                sv_json = json.dumps(sv) if isinstance(sv, list) else None

                # trend_pct 계산 (없으면 sparkline에서 계산)
                tpct = item.get("trend_pct")
                if tpct is None and isinstance(sp, list) and len(sp) >= 2:
                    valid = [p for p in sp if p is not None]
                    if len(valid) >= 2:
                        tpct = (valid[-1] - valid[0]) / valid[0] * 100

                record = ScreenerResult(
                    market=market,
                    symbol=item["symbol"],
                    name=item["name"],
                    current_price=item.get("current_price"),
                    entry_score=item.get("entry_score"),
                    eval_score=item.get("eval_score"),
                    total_score=item.get("total_score"),
                    rationale=item.get("rationale"),
                    sector=item.get("sector"),
                    analyst_rating=item.get("analyst_rating"),
                    analyst_rating_raw=item.get("analyst_rating_raw"),
                    analyst_count=item.get("analyst_count"),
                    trend_pct=tpct,
                    sparkline_prices=sp_json,
                    sparkline_volumes=sv_json,
                    created_at=scan_time
                )
                db_records.append(record)
                
        if db_records:
            db.bulk_save_objects(db_records)
            db.commit()
            logger.info(f"Successfully saved {len(db_records)} screener results for {market} to the database.")
            db.close()
            return True
            
        db.close()
        return False
    except Exception as e:
        logger.error(f"Error during saving screener results to database: {str(e)}")
        return False

def get_top_screener_results(limit: int = 10, market: str = None) -> List[Dict[str, Any]]:
    """Retrieve the latest top screener results sorted by total_score."""
    global SessionLocal
    if SessionLocal is None:
        if not init_db():
            return []
    try:
        db = SessionLocal()
        # Find the latest scan time
        query = db.query(ScreenerResult)
        if market:
            query = query.filter(ScreenerResult.market == market)
            
        latest_record = query.order_by(ScreenerResult.created_at.desc()).first()
        if not latest_record:
            db.close()
            return []
            
        latest_time = latest_record.created_at
        
        # Query results from that scan time
        res_query = db.query(ScreenerResult).filter(ScreenerResult.created_at == latest_time)
        if market:
            res_query = res_query.filter(ScreenerResult.market == market)
            
        results = res_query.order_by(ScreenerResult.total_score.desc()).limit(limit).all()
        
        import json
        dict_results = []
        for r in results:
            dict_results.append({
                "market": r.market,
                "symbol": r.symbol,
                "name": r.name,
                "current_price": r.current_price,
                "entry_score": r.entry_score,
                "eval_score": r.eval_score,
                "total_score": r.total_score,
                "rationale": r.rationale,
                "sector": r.sector,
                "analyst_rating": r.analyst_rating,
                "analyst_rating_raw": r.analyst_rating_raw,
                "analyst_count": r.analyst_count,
                "trend_pct": r.trend_pct,
                "sparkline_prices": json.loads(r.sparkline_prices) if r.sparkline_prices else None,
                "sparkline_volumes": json.loads(r.sparkline_volumes) if r.sparkline_volumes else None,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            })
        db.close()
        return dict_results
    except Exception as e:
        logger.error(f"Error retrieving top screener results: {str(e)}")
        return []

def get_latest_score_by_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent score for a specific ticker symbol."""
    global SessionLocal
    if SessionLocal is None:
        if not init_db():
            return None
    try:
        db = SessionLocal()
        symbol_upper = symbol.upper()
        # Find latest record for this exact symbol (or matching the prefix if exact fails, though usually exact)
        record = db.query(ScreenerResult).filter(
            ScreenerResult.symbol == symbol_upper
        ).order_by(ScreenerResult.created_at.desc()).first()
        
        if not record:
            # Fallback for Yahoo format mapping if they omitted suffix
            record = db.query(ScreenerResult).filter(
                ScreenerResult.symbol.startswith(symbol_upper)
            ).order_by(ScreenerResult.created_at.desc()).first()
            
        if not record:
            db.close()
            return None
            
        import json
        res = {
            "market": record.market,
            "symbol": record.symbol,
            "name": record.name,
            "current_price": record.current_price,
            "entry_score": record.entry_score,
            "eval_score": record.eval_score,
            "total_score": record.total_score,
            "rationale": record.rationale,
            "sector": record.sector,
            "analyst_rating": record.analyst_rating,
            "analyst_rating_raw": record.analyst_rating_raw,
            "analyst_count": record.analyst_count,
            "trend_pct": record.trend_pct,
            "sparkline_prices": json.loads(record.sparkline_prices) if record.sparkline_prices else None,
            "sparkline_volumes": json.loads(record.sparkline_volumes) if record.sparkline_volumes else None,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else ""
        }
        db.close()
        return res
    except Exception as e:
        logger.error(f"Error retrieving score for {symbol}: {str(e)}")
        return None

