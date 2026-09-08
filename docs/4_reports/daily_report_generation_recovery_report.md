# 📄 일일 투자 보고서 생성 장애 원인 분석 및 복구 보고서 (Daily Report Recovery Report)

## 1. 📌 장애 개요
- **장애 기간**: 2026-08-24 ~ 2026-09-09
- **장애 현상**: 2026년 8월 24일부터 아침 06:00 정기 배치 크론잡이 실행되지 않아 일일 투자 전략 보고서가 생성되지 않았으며, 실시간 웹 대시보드(스마트 아카이브)에 8월 23일자 보고서까지만 노출되는 현상 발생.
- **영향 범위**:
  - 원격 VPS(cafe24 Linux) 백그라운드 크론 파이프라인(`run_pipeline.sh`) 중단
  - 일일 시장/거시지표/유튜브 요약 및 Google Gemini AI 리포트 생성 중단
  - MariaDB `daily_reports` 테이블 인덱싱 누락으로 인한 프론트엔드 아카이브 동기화 중단

---

## 2. 🔍 근본 원인 분석 (Root Cause Analysis)

조사 결과, **Linux(cafe24) 서버 인프라 환경 설정 불일치**와 **코드베이스 상의 누락**이 복합적으로 결합하여 발생한 것으로 확인되었습니다.

### 1) [Linux/cafe24] 프로젝트 디렉터리 이름 변경 후 `venv` 경로 불일치
- 8월 23일 프로젝트 표준 명칭 리팩토링 과정에서 서버 디렉터리가 `/root/stockRecommnad` &rarr; `/root/stockRecommend`로 변경되었습니다.
- 그러나 파이썬 가상환경(`venv`) 내부의 스크립트 셔뱅(shebang: `venv/bin/pip`)과 활성화 스크립트(`venv/bin/activate`)에 기존 구형 경로(`/root/stockRecommnad/...`)가 하드코딩된 상태로 잔류하였습니다.
- 이로 인해 매일 06:00 크론잡(`run_pipeline.sh`)이 `source "$VENV_DIR/bin/activate"`를 실행했으나 유효하지 않은 경로가 `PATH`에 등록되어 가상환경이 정상 활성화되지 못했습니다.

### 2) [Linux/cafe24] 전역 시스템 파이썬 오염 및 OpenSSL 라이브러리 충돌
- 가상환경이 비활성화된 상태에서 `run_pipeline.sh`의 의존성 설치 명령(`pip install -r requirements.txt`)이 호출되면서, 패키지들이 **리눅스 OS 전역 시스템 파이썬 환경(`/usr/local/lib/python3.10/dist-packages`)**에 강제 설치되었습니다.
- 이 과정에서 새로 설치된 최신 `cryptography (50.0.0)`와 Ubuntu 시스템 기본 패키지인 `pyOpenSSL (21.0.0)` 간의 C 바인딩 버전 충돌이 발생하였습니다.
  ```text
  File "/usr/lib/python3/dist-packages/OpenSSL/crypto.py", line 813, in X509Extension
      _lib.GEN_EMAIL: "email",
  AttributeError: module 'lib' has no attribute 'GEN_EMAIL'
  ```
- 이후 `run_pipeline.sh`가 시스템 파이썬(`/usr/bin/python3`)으로 `main.py`를 실행할 때마다 `FinanceDataReader` &rarr; `urllib3` &rarr; `pyOpenSSL` 임포트 과정에서 1초 만에 `GEN_EMAIL` 치명적 오류로 크래시(exit code 1)되었습니다.

### 3) [코드베이스] `main.py` 내 `import re` 누락으로 인한 DB 인덱싱 실패
- 8월 23일 일일 리포트 스마트 아카이브 커밋(`336d0a8`) 당시, [main.py](file:///c:/Users/samsung/proj/stockRecommend/main.py) 하단에 정규표현식(`re.search`)을 활용한 DB 인덱싱 로직이 추가되었으나 파일 상단에 `import re`가 누락되어 있었습니다.
- 그 결과 설령 파이프라인이 구동되었더라도 `name 're' is not defined` 예외가 발생하여 MariaDB의 `daily_reports` 테이블에 보고서가 적재되지 않는 결함이 존재했습니다.

---

## 3. 🛠️ 해결 방안 및 조치 내역

### 1) 원격 Linux OS 시스템 파이썬 패키지 호환성 복구
- cafe24 서버 전역 시스템 파이썬의 `pyOpenSSL`을 최신 호환 버전(26.4.0)으로 업그레이드하여 시스템 레벨의 `GEN_EMAIL` 충돌을 해소했습니다.

### 2) 가상환경(`/root/stockRecommend/venv`) 클린 재구축
- 손상된 기존 venv 디렉터리를 완전히 제거하고 신규 생성한 뒤, [requirements.txt](file:///c:/Users/samsung/proj/stockRecommend/requirements.txt)의 모든 의존성을 깨끗하게 재설치했습니다 (`Venv OK!` 검증 완료).

### 3) 스케줄러 스크립트([run_pipeline.sh](file:///c:/Users/samsung/proj/stockRecommend/run_pipeline.sh)) 방어 로직 강화
- **명시적 가상환경 바이너리 호출**: 쉘의 환경 변수 오염 여부에 영향을 받지 않도록 `"$VENV_PYTHON" "$PROJECT_DIR/main.py"`와 같이 가상환경의 파이썬 인터프리터를 직접 지정하도록 수정했습니다.
- **불필요한 일일 pip install 제거**: 매일 크론 실행 시마다 pip 패키지를 반복 검사/설치하여 시스템을 오염시키고 네트워크 지연을 유발하던 코드를 제거하고, venv 최초 생성 시에만 1회 설치되도록 최적화했습니다.

### 4) [main.py](file:///c:/Users/samsung/proj/stockRecommend/main.py) 정규표현식 임포트 및 추천 태그 인덱싱 고도화
- 상단에 누락된 `import re`를 추가했습니다.
- 리포트 마크다운 본문의 매수/매도 종목 테이블을 자동 파싱하여 `recommended_stocks` 필드에 JSON으로 함께 저장하도록 개선하여, 대시보드 상에서 `[BUY] 엔비디아 (NVDA)`, `[BUY] 삼성전자 (005930)` 등 추천 태그가 노출되도록 보강했습니다.

### 5) 원격 MariaDB 보고서 전체 복구 및 백필 (Backfill)
- 원격 서버에서 파이프라인을 테스트 실행하여 최신 보고서(`2026-09-08_report.md`)를 정상 생성했습니다.
- 원격 MariaDB의 `daily_reports` 테이블에 과거 누락분을 포함한 총 72건의 보고서 데이터를 전수 색인 완료했습니다.

---

## 4. ✅ 검증 결과

| 검증 항목 | 검증 내용 | 결과 |
| :--- | :--- | :---: |
| **원격 파이프라인 수동 테스트** | `main.py` 실행 (시장 데이터 수집, Gemini LLM 리포트 작성, DB 인덱싱) | **성공 (정상 생성)** |
| **원격 MariaDB 정합성** | `DailyReport` 레코드 수 및 최신 생성 일자 확인 | **총 72건, 최신 2026-09-08 반영** |
| **실시간 라이브 UI 검증** | `https://stockrecommend.vercel.app/` 스마트 아카이브 화면 확인 | **정상 렌더링 확인 (스크린샷 검증)** |
| **로컬 단위/통합 테스트** | `pytest tests/` 79개 테스트 케이스 실행 | **79 Passed (100% 통과)** |
| **원격 데몬 및 스케줄러** | `stock-recommend.service` 및 crontab(`0 6 * * *`) 등록 상태 점검 | **정상 구동 중 (Active: running)** |

---

## 5. 💡 향후 재발 방지 대책
1. **서버 디렉터리 경로 변경 시 venv 재생성 원칙 수립**: 가상환경은 이동하지 않고 항상 신규 생성 후 `pip install` 진행.
2. **크론 배치 스크립트 내 절대 경로 파이썬 바이너리 사용**: `source activate`에 의존하지 않고 `"$PROJECT_DIR/venv/bin/python"` 직접 실행.
3. **정기 스케줄러 상태 모니터링**: 텔레그램 봇(`/system`) 또는 일일 파이프라인 실패 알림 웹훅 연동 유지.
