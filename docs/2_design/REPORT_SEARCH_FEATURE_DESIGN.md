# 🔍 일일 투자 리포트 웹 검색 시스템 설계서 (Report Search Feature Design)

본 문서는 매일 아침 자동 생성되는 일일 종합 투자 리포트(Daily Investment Reports)를 Vercel 웹 대시보드에서 즉시 검색·열람하고 종목별 추천 이력을 추적할 수 있도록 지원하는 **리포트 웹 아카이브 및 스마트 검색 시스템**의 상세 설계서입니다.

---

## 🎯 1. 기능 목표 및 기대 효과

1. **과거 리포트 아카이브 열람**: 일자별 리포트를 마크다운 뷰어 및 구글 드라이브 문서 링크와 함께 제공
2. **초고속 전문 검색 (Full-Text Search)**: SQLite 내장 `FTS5` 엔진을 활용하여 리포트 본문, AI 거시 경제 요약, 종목 분석 내용 실시간 검색
3. **종목별 추천 히스토리 추적**: 특정 종목(예: 삼성전자, NVDA)의 과거 매수/매도/홀딩 추천 일자 및 당시 AI 평가 이력 필터링
4. **사용자 편의성 극대화**: Vercel 프론트엔드 대시보드에 직관적인 검색 UI 및 모달/전용 뷰어 제공

---

## 🏗️ 2. 시스템 아키텍처

```mermaid
flowchart TD
    subgraph Daily_Pipeline [일일 자동화 파이프라인 (매일 06:00 KST)]
        Main[main.py / run_pipeline.sh] --> GenReport[Gemini AI 리포트 생성]
        GenReport --> FileSave[reports/YYYY-MM-DD_report.md 저장]
        GenReport --> GDrive[Google Drive 업로드]
        GenReport --> Indexer[Report Indexer 모듈]
    end

    subgraph Database_Layer [데이터베이스 레이어 (SQLite)]
        Indexer --> ReportDB[(stock_db.sqlite)]
        ReportDB --- MetaTable[reports 메타 테이블]
        ReportDB --- FTSTable[reports_fts 전문 검색 테이블]
    end

    subgraph Backend_API [FastAPI 웹 서버 (Cafe24 VPS)]
        ReportDB --> SearchAPI[GET /api/reports/search]
        ReportDB --> ListAPI[GET /api/reports]
        ReportDB --> DetailAPI[GET /api/reports/:id]
    end

    subgraph Frontend_UI [Vercel 웹 대시보드]
        SearchAPI --> WebUI[리포트 아카이브 & 검색 탭]
        ListAPI --> WebUI
        DetailAPI --> WebUI
    end
```

---

## 📊 3. 데이터베이스 스키마 설계

`stock_db.sqlite` 내에 리포트 메타데이터 테이블과 FTS5 가상 테이블을 생성합니다.

```sql
-- 1. 리포트 메타데이터 테이블
CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL UNIQUE,       -- 'YYYY-MM-DD'
    title TEXT NOT NULL,                   -- '2026-08-23 Daily Stock Discovery Report'
    macro_summary TEXT,                    -- AI 거시 경제 요약 요약문
    recommended_stocks TEXT,               -- 추천 종목 JSON 문자열: [{"symbol":"AAPL","action":"BUY"}, ...]
    rebalance_actions TEXT,                -- 리밸런싱 요약 JSON 문자열
    file_path TEXT NOT NULL,               -- 'reports/2026-08-23_report.md'
    gdrive_link TEXT,                      -- Google Doc URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 전문 검색(Full-Text Search) 가상 테이블 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS reports_fts USING fts5(
    report_date,
    title,
    macro_summary,
    content,                               -- 리포트 전체 마크다운 본문
    content='daily_reports',
    content_rowid='id'
);
```

---

## 🔌 4. 백엔드 API 명세 (FastAPI)

### 1) 리포트 전문 검색 API
* **Endpoint**: `GET /api/reports/search`
* **Query Parameters**:
  * `q` (string, optional): 검색 키워드 (예: `"금리"`, `"삼성전자"`, `"NVDA"`)
  * `symbol` (string, optional): 특정 종목 티커 (예: `"005930.KS"`)
  * `action` (string, optional): 추천 액션 (`BUY`, `SELL`, `HOLD`)
  * `from_date` (string, optional): 시작일 (`YYYY-MM-DD`)
  * `to_date` (string, optional): 종료일 (`YYYY-MM-DD`)
  * `page` / `limit`: 페이징 번호 및 개수 (기본 10건)
* **Response 예시**:
```json
{
  "total": 5,
  "page": 1,
  "results": [
    {
      "id": 12,
      "report_date": "2026-08-23",
      "title": "2026-08-23 Daily Stock Discovery Report",
      "macro_summary": "환율 1,380원대 안정화 및 반도체 섹터 외국인 순매수 지속...",
      "highlight": "삼성전자(005930.KS)의 <b>CANSLIM</b> 성장 지표 개선으로...",
      "recommended_stocks": [
        {"symbol": "005930.KS", "name": "Samsung Electronics", "action": "BUY", "score": 85}
      ],
      "gdrive_link": "https://docs.google.com/document/d/..."
    }
  ]
}
```

---

## 💻 5. 프론트엔드 UI 화면 기획 (Vercel)

1. **상단 필터 바**:
   - 통합 검색 입력창 (키워드 실시간 하이라이팅)
   - 날짜 범위 피커 (최근 1주일, 1개월, 3개월, 사용자 지정)
   - 액션 필터 버튼 (전체 / 🟢 BUY만 보기 / 🔴 SELL만 보기)
2. **리포트 타임라인 카드 목록**:
   - 일자별 카드: 리포트 날짜, 주요 AI 한 줄 요약, 추천 종목 태그 뱃지
   - 클릭 시 우측 슬라이드 패널 또는 모달에서 마크다운 리포트 전문 즉시 렌더링
   - `Google Doc으로 열기` 새 창 버튼 제공

---

## 🚀 6. 구현 단계 계획 (명칭 변경 후 진행)

* **Phase 1**: `daily_reports` & `reports_fts` DB 테이블 생성 및 `main.py` 리포트 저장 시 자동 인덱싱 로직 추가
* **Phase 2**: 기존에 축적된 `reports/*.md` 파일 일괄 백필(Backfill) 인덱싱 스크립트 실행
* **Phase 3**: FastAPI `/api/reports/search` 엔드포인트 구현 및 단위 테스트 작성
* **Phase 4**: Vercel 프론트엔드(`index.html`, `app.js`, `style.css`)에 리포트 검색 탭 구축 및 배포
