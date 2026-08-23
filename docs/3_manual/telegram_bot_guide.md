# Antigravity 2.0 Telegram Bot 가이드 (Telegram Control Guide)

이 가이드는 모바일 텔레그램을 통해 **Antigravity 2.0 AI 코딩 에이전트**에게 명령을 내리고 로컬 시스템 상태를 모니터링할 수 있도록 텔레그램 봇을 생성하고 연동하는 절차를 설명합니다.

---

## 1. 텔레그램 봇 생성 및 설정 (Prerequisites)

### 1단계: Bot Token 발급받기
1. 텔레그램 앱에서 **@BotFather**를 검색하여 대화를 시작합니다.
2. `/newbot` 명령어를 전송합니다.
3. 봇의 이름(Name)과 사용자명(Username, 반드시 `_bot`으로 끝나야 함)을 입력합니다.
4. 생성이 완료되면 제공되는 **HTTP API Token** (예: `1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ`)을 복사합니다.

### 2단계: 본인의 Chat ID 확인하기
안전한 전용 채널을 만들기 위해 본인의 텔레그램 계정 ID(Chat ID)를 조회하여 등록해야 합니다. (타인 접근 불가)
1. 텔레그램 앱에서 **@userinfobot** 또는 **@GetIDBot**을 검색하여 대화를 시작합니다.
2. `/start`를 전송하면 본인의 **ID 숫자가 출력**됩니다. (예: `987654321`)
3. 이 숫자를 복사해 둡니다.

---

## 2. 환경 변수 구성 (`.env` 파일 수정)

프로젝트 루트 디렉토리의 [`.env`](file:///c:/Users/samsung/proj/stockRecommend/.env) 파일을 열고, 맨 아래에 복사해 둔 값을 입력합니다:

```env
# --- TELEGRAM BOT CONFIGURATION ---
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=987654321
```

---

## 3. 텔레그램 봇 실행 및 테스트

### 로컬 PC에서 봇 구동하기
터미널을 열고 가상환경 파이썬 인터프리터를 이용해 봇 데몬을 실행합니다:

```bash
# Windows PowerShell 기준
c:\Users\samsung\proj\stockRecommend\venv\Scripts\python.exe c:\Users\samsung\proj\antigravity_bot.py
```

실행 시 봇이 가동되며 등록된 텔레그램으로 아래와 같은 알림이 전송됩니다.
> 🤖 **Antigravity 2.0 Agent Bot**이 가동되었습니다!
> /help 명령어로 지원되는 명령어를 확인해 보세요.

---

## 4. 텔레그램 명령어 사용법

봇 대화창에 명령어를 입력해 모바일로 제어합니다. 아래 명령어 중 시스템 상태 변경 및 파일 조작 등 보안 위협이 따르는 기능은 텔레그램 상에서 사용자의 명시적인 승인 단계를 거칩니다.

### 📊 조회 및 모니터링 명령어
* **`/system`** : 로컬 PC의 CPU 사용량, 사용 중인 메모리 리소스, 디스크 여유 공간 및 활성 프로젝트 경로를 실시간 조회합니다.
* **`/status`** : 백그라운드에서 실행 중인 실시간 주식 스크리너의 상태(진행률, 현재 분석 중인 티커 등)를 확인합니다.
* **`/screener [시장명]`** : 각 시장별 최상위 추천 종목 10개를 퀀트 분석 사유와 함께 요약 표시합니다. (예: `/screener kospi`, `/screener sp500`, `/screener kosdaq`)
* **`/score <티커>`** : 특정 개별 종목의 퀀트 분석 점수(진입 점수 및 평가 점수)와 Rationale을 즉시 조회합니다. (예: `/score AAPL`)

### ⚙️ 워크스페이스 제어 명령어
* **`/project [경로]`** : 
  - 인자 없이 호출 시: 현재 봇이 바라보고 있는 활성 프로젝트 디렉토리 경로를 표시합니다.
  - 경로와 함께 호출 시: 해당 디렉토리로 워크스페이스를 동적으로 전환(Hot-reload)합니다. 새 프로젝트의 `.env`, `sys.path`, DB 커넥션, 제미나이 에이전트 모델 설정이 자동으로 즉각 갱신됩니다. (예: `/project c:\Users\samsung\proj\stockScreener`)

### 💻 실행 및 에이전트 제어 명령어 (승인 필요)
* **`/cmd <명령어>`** : 로컬 터미널의 cmd 명령을 직접 실행합니다.
  - 예: `/cmd git status` (git 상태 확인)
  - 예: `/cmd venv\Scripts\python.exe -m pytest tests/`
* **`/chat <작업지시>` 또는 일반 대화** : **AI 코딩 에이전트(Antigravity 2.0)**에게 자연어로 작업을 지시합니다.
  - 에이전트는 파일 읽기(`read_file`), 쓰기(`write_file`), 폴더 내용 보기(`list_dir`), 터미널 실행(`run_command`) 도구를 자유자재로 사용하여 로컬 코드를 변경하거나 테스트를 수행합니다.
  - 예: `/chat scoring.py에 주석을 한글로 보완하고 테스트 돌려서 결과 알려줘`

---

## 🔒 대화형 원격 안전 승인 (Remote Approval)

시스템의 무단 변경 및 오작동을 예방하기 위해, 명령어 실행 및 에이전트 도구 실행 전 안전장치(Approval Lock)가 가동됩니다:

1. **승인 요청 전송**: `/cmd` 실행 또는 에이전트가 코드를 수정하려 하거나(`write_file`), 터미널 명령을 수행하려 할 때(`run_command`), 아래와 같이 인라인 승인 요청 메시지가 발송됩니다.
   > ⚠️ **원격 승인 요청 (run_command)**
   > 📄 **상세 정보**: `venv\Scripts\python -m pytest tests/`
   > 이 작업을 실행하시겠습니까?
   > `[✅ 승인]` `[❌ 반려]`
2. **동작 처리**:
   - 사용자가 **`[✅ 승인]`**을 누르면 차단이 해제되어 명령이 실행되고 결과가 피드백됩니다.
   - 사용자가 **`[❌ 반려]`**를 누르거나 5분간 응답하지 않을 경우(Timeout), 작업이 즉각 취소되고 에러 로그가 전달됩니다.
3. **마크다운 예외 처리**: 에이전트 답변이 비정상적으로 잘려 마크다운 태그 오류가 발생할 경우, 봇이 다운되지 않고 즉시 평문 모드로 변환하여 안정적으로 메시지를 렌더링합니다.

