"""
naver_finance.py

FinanceDataReader를 통해 한국 거래소(KRX) 종목의 섹터/업종 정보를 제공합니다.
FinanceDataReader는 무료이며 API 키가 필요 없습니다.

한국 주식 애널리스트 의견은 공개 무료 API가 없으므로 yfinance fallback을 사용합니다.
"""

import threading
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# 캐시: 24시간 TTL
_krx_sector_cache: Dict[str, Dict[str, str]] = {}  # code -> {sector, industry}
_cache_lock = threading.Lock()
_cache_loaded_at: float = 0.0
_CACHE_TTL_SEC = 86400  # 24시간


def _load_krx_listing() -> Dict[str, Dict[str, str]]:
    """FinanceDataReader로 KRX 전체 종목 섹터/업종 로드 (캐시 적용)."""
    global _krx_sector_cache, _cache_loaded_at

    with _cache_lock:
        now = time.time()
        if _krx_sector_cache and (now - _cache_loaded_at) < _CACHE_TTL_SEC:
            return _krx_sector_cache

        try:
            import FinanceDataReader as fdr
            df = fdr.StockListing('KRX')
            result = {}
            for _, row in df.iterrows():
                code = str(row.get('Code', '') or row.get('Symbol', '')).strip()
                if not code:
                    continue
                sector = str(row.get('Sector', '') or row.get('Industry', '') or '').strip()
                industry = str(row.get('Industry', '') or '').strip()
                if not sector and not industry:
                    sector = str(row.get('Market', '')).strip()
                result[code] = {
                    'sector': sector or None,
                    'industry': industry or None,
                }
            _krx_sector_cache = result
            _cache_loaded_at = now
            logger.info(f"[naver_finance] KRX 종목 섹터 데이터 로드 완료: {len(result)}개")
            return result
        except Exception as e:
            logger.warning(f"[naver_finance] KRX 섹터 로드 실패: {e}")
            return _krx_sector_cache  # 이전 캐시 반환


def get_krx_sector(ticker: str) -> Dict[str, Optional[str]]:
    """
    .ks/.KS 또는 6자리 코드에서 KRX 섹터/업종 정보를 반환합니다.

    Args:
        ticker: 예) "005930.ks", "005930.KS", "005930"

    Returns:
        {"sector": "전기전자", "industry": "반도체"}  또는 None 값 포함
    """
    # 티커에서 순수 종목코드 추출 (예: "005930.ks" -> "005930")
    code = ticker.upper().replace('.KS', '').replace('.KQ', '').replace('.KRX', '').strip()

    listing = _load_krx_listing()
    if code in listing:
        return listing[code]

    return {'sector': None, 'industry': None}


def enrich_with_krx_sector(ticker: str, existing_sector: Optional[str], existing_industry: Optional[str]) -> Dict[str, Optional[str]]:
    """
    기존 sector/industry가 None이거나 비어있으면 KRX 데이터로 보완합니다.
    """
    if existing_sector and existing_industry:
        return {'sector': existing_sector, 'industry': existing_industry}

    is_korean = '.ks' in ticker.lower() or '.kq' in ticker.lower()
    if not is_korean:
        return {'sector': existing_sector, 'industry': existing_industry}

    krx_data = get_krx_sector(ticker)
    return {
        'sector': existing_sector or krx_data.get('sector'),
        'industry': existing_industry or krx_data.get('industry'),
    }
