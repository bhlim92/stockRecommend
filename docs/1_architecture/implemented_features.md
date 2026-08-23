# 주식 발굴 및 포트폴리오 리밸런싱 시스템: 구현 기능 명세서

본 문서는 프로젝트에 실제 구현 및 배포 완료되어 안정적으로 동작하고 있는 전체 시스템 기능의 상세 사양 및 파일 매핑 정보를 제공합니다.

---

## 📊 1. 배치 데이터 파이프라인 (Batch Data Pipeline)
매일 아침 자동으로 실행되어 거시경제 정보, 기업 시세 데이터, 뉴스 및 외부 전문가 의견을 수집/분석하고 요약 보고서를 생성 및 배포합니다.

| 기능명 | 구현 세부 사양 | 관련 주요 코드 및 파일 |
| :--- | :--- | :--- |
| **일일 자동 스케줄링** | Windows 작업 스케줄러를 통해 매일 아침 06:00에 가상환경 진입 및 실행 프로세스를 자동으로 시작합니다. | [`run_pipeline.bat`](file:///c:/Users/samsung/proj/stockRecommend/run_pipeline.bat)<br>[`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |
| **시장 데이터 수집** | - `yfinance` 및 `FinanceDataReader` 연동<br>- 국내 및 해외 관심 종목 시세 수집<br>- 환율(USD/KRW) 및 미국채 10년물 금리 등 거시 지표 수집 | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py)<br>[`app/config.py`](file:///c:/Users/samsung/proj/stockRecommend/app/config.py) |
| **뉴스 RSS 스크래핑** | Google News, Yahoo Finance, Naver News 등 주요 채널의 실시간 경제 뉴스 RSS 피드를 자동으로 스크랩하고 파싱합니다. | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |
| **유튜브 자막 분석** | 설정된 전문가 유튜브 채널의 최신 비디오를 감지하고, 자막이 활성화된 경우 자막 텍스트를 통째로 다운로드하여 요약 자료로 전환합니다. (실패 시 설명/제목 대체 예외 처리 내장) | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |
| **AI 리포트 자동 생성** | 수집된 데이터(뉴스, 유튜브 자막, 가격 변동 등)를 Gemini API에 전송하여 오늘의 투자 브리핑 및 포트폴리오 제안서 마크다운 리포트를 자동 작성합니다. | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |
| **구글 드라이브 업로드** | 생성된 마크다운 리포트를 Google Cloud Service Account를 활용하여 지정된 공유 드라이브 폴더에 자동 업로드하고 공유 링크를 발급받습니다. | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |
| **아침 텔레그램 브리핑** | 매일 아침 08:00에 파이프라인 분석 결과와 상위 추천 종목 브리핑을 텔레그램 메시지로 자동 전송합니다. | [`main.py`](file:///c:/Users/samsung/proj/stockRecommend/main.py) |

---

## 🎨 2. 프리미엄 웹 대시보드 (Web Server & Dashboard)
사용자 관점에서 자산 현황을 모니터링하고 Gemini AI의 실시간 포트폴리오 리밸런싱 피드백을 받을 수 있는 웹 프론트엔드 및 백엔드 서버입니다.

| 기능명 | 구현 세부 사양 | 관련 주요 코드 및 파일 |
| :--- | :--- | :--- |
| **프리미엄 HSL UI** | - Sleek Dark Mode HSL 테마 바탕 화면 구현<br>- Glassmorphism 반투명 유리 효과 적용<br>- 모바일 및 태블릿에 대응하는 완전 반응형 레이아웃 설계 | [`index.html`](file:///c:/Users/samsung/proj/stockRecommend/app/static/index.html)<br>[`style.css`](file:///c:/Users/samsung/proj/stockRecommend/app/static/style.css) |
| **통합 자산 관리 테이블** | - 일반 주식 계좌와 개인 연금 계좌의 실시간 자산 현황을 동시에 파싱하여 단일 테이블에 연동<br>- 계좌별 특성을 강조하기 위한 HSL 뱃지 적용 | [`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js)<br>[`index.html`](file:///c:/Users/samsung/proj/stockRecommend/app/static/index.html) |
| **실시간 지표 연동 API** | - yfinance `fast_info`를 사용하여 KOSPI 지수 및 S&P 500 지수의 최종 거래 가격과 당일 등락률을 5분 캐시 기반으로 서빙<br>- open.er-api 연동을 통한 USD/KRW 환율 실시간 자동 환산 적용 | [`web_server.py`](file:///c:/Users/samsung/proj/stockRecommend/app/web_server.py)<br>[`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js) |
| **브라우저 캐시 방지** | 정적 리소스(JS/CSS) 및 API 요청 시 강력한 브라우저 캐싱으로 인해 이전 데이터가 나오는 것을 차단하기 위해 타임스탬프 파라미터(`?v=3.5`, `?_t=`)를 강제 삽입합니다. | [`index.html`](file:///c:/Users/samsung/proj/stockRecommend/app/static/index.html)<br>[`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js) |
| **AI 리밸런싱 컨설턴트** | - 버튼 클릭 시 백엔드를 통해 Gemini LLM이 현재 자산의 드리프트(목표 비중 대비 이탈 정도)를 비교 분석하고 상세 BUY/SELL/HOLD 주문 추천서를 실시간 렌더링<br>- Gemini API Rate Limit 보호를 위한 13초 대기 카운트다운 게이지 UI 적용 | [`web_server.py`](file:///c:/Users/samsung/proj/stockRecommend/app/web_server.py)<br>[`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js) |
| **CLS 방지 스켈레톤 로더** | 자산 정보 및 AI 컨설팅 데이터 로딩 시 투박한 로딩 스피너 대신 흔들림 없는 펄스(Pulse)형 레이아웃 스켈레톤 로더를 표출하여 사용성을 향상시킵니다. | [`style.css`](file:///c:/Users/samsung/proj/stockRecommend/app/static/style.css)<br>[`index.html`](file:///c:/Users/samsung/proj/stockRecommend/app/static/index.html) |
| **시각화 차트 그라디언트** | Chart.js 캔버스 영역에 리니어 그라디언트(Linear Gradient)를 동적으로 삽입하여 네온 글로우 스타일의 비중 차트를 렌더링합니다. | [`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js) |

---

## ⚡ 3. 실시간 주식 스크리너 (Stock Screener)
수백 개 종목에 대한 계량적 가치 및 거래량 지표를 병렬로 스캔하여 최상위 퀀트 추천 주식을 선별하는 핵심 스크리너 엔진입니다.

| 기능명 | 구현 세부 사양 | 관련 주요 코드 및 파일 |
| :--- | :--- | :--- |
| **멀티 스레드 병렬 스캔** | `ThreadPoolExecutor(max_workers=15)`를 기동하여 KOSPI 200, KOSDAQ, S&P 500 등 500개 이상의 종목 데이터를 단 30초 내에 전수 수집 및 평가합니다. | [`screener.py`](file:///c:/Users/samsung/proj/stockRecommend/app/screener.py)<br>[`web_server.py`](file:///c:/Users/samsung/proj/stockRecommend/app/web_server.py) |
| **CANSLIM Scoring 퀀트 로직** | PER, PEG, EPS 성장률, 기관 수급, 가격 추세 등 윌리엄 오닐의 CANSLIM 투자 전략을 수치화하여 종합 점수를 산출합니다. | [`scoring.py`](file:///c:/Users/samsung/proj/stockRecommend/app/scoring.py) |
| **실시간 폴링 및 리더보드** | - 브라우저 단에서 2.0초 간격으로 스캔률과 진행 현황을 백엔드로부터 비동기 수집<br>- 진행 중 브라우저 DOM 부하를 예방하기 위해 전체 종목이 아닌 상위 15개의 실시간 리더보드만 지속 렌더링 | [`screener.html`](file:///c:/Users/samsung/proj/stockRecommend/app/static/screener.html)<br>[`app.js`](file:///c:/Users/samsung/proj/stockRecommend/app/static/app.js) |
| **DB 스냅샷 백업** | 분석 완료된 전체 리스트 점수 결과는 RDBMS(데이터베이스)에 즉시 스냅샷으로 기록 보관하여 이력 관리를 보장합니다. | [`screener.py`](file:///c:/Users/samsung/proj/stockRecommend/app/screener.py) |

---

## 🔒 4. 텔레그램 원격 제어 및 안전 승인 (Telegram Control & Approval)
모바일 메신저로 전체 PC 서버를 모니터링하고 안전한 통제 하에 원격 개발 및 쉘 실행을 수행하도록 중재하는 상주형 데몬입니다.

| 기능명 | 구현 세부 사양 | 관련 주요 코드 및 파일 |
| :--- | :--- | :--- |
| **상태 및 리더보드 조회** | - `/system`: CPU, RAM, Disk, Active Workspace 경로 실시간 조회<br>- `/status`: 스크리너 진행률 조회<br>- `/screener [시장]`: 각 시장별 최상위 추천 종목 Top 10을 근거와 함께 마크다운 수신<br>- `/score <티커>`: 특정 종목의 CANSLIM 세부 지표 수치 즉시 조회 | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py) |
| **원격 CLI 제어 및 AI 코딩** | - `/cmd <명령>`: 로컬 cmd 명령을 즉시 구동하고 표준 출력/에러 수신<br>- `/chat <지시>`: AI 에이전트(Antigravity 2.0)를 실행하여 로컬 소스 코드를 읽고/쓰고/테스트하는 자율 코딩 시작 | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py) |
| **인라인 키보드 원격 안전 승인** | - 보안 위협이 되는 파일 쓰기(`write_file`), 도구 실행(`run_command`), 터미널 명령어 실행(`/cmd`) 시 텔레그램 창에 `[✅ 승인]`, `[❌ 반려]` 인라인 버튼 송신<br>- 사용자의 명시적인 클릭 피드백이 올 때까지 백그라운드 스레드를 대기 상태로 차단 | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py) |
| **스레드 안전 대기 잠금** | 비동기 봇 이벤트 루프를 막지 않고 백그라운드 호출을 차단하기 위해 스레드 안전 `threading.Event()`와 고유 요청 ID 매핑 메커니즘 사용 | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py) |
| **프로젝트 동적 전환** | - `/project [경로]` 명령어를 통해 봇이 실행하는 기본 워크스페이스 위치 전환<br>- 활성 디렉토리 변경 시 `.env` 리로드, `sys.path` 갱신, DB 및 제미나이 봇 모델 재구성을 동적으로 수행 (설정은 `bot_config.json`에 영구 보존) | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py)<br>[`bot_config.json`](file:///c:/Users/samsung/proj/bot_config.json) |
| **Markdown 파싱 예외 복구** | Gemini 에이전트의 불완전한 문장 커팅 등으로 텔레그램 마크다운 파싱 에러 발생 시, 메시지 송신 실패를 방지하기 위해 `safe_` 메시지 래퍼 함수를 적용하여 즉각 일반 평문(`parse_mode=None`)으로 자동 우회 전송합니다. | [`antigravity_bot.py`](file:///c:/Users/samsung/proj/antigravity_bot.py) |
