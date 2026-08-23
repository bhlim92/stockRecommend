# 'stockrecommand' -> 'stockRecommend' 일괄 변경 계획 (전문가 패널 검토 반영본)

프로젝트 전반(문서, 디렉터리, 스크립트, 설정 파일)에 혼재되어 있는 `stockrecommand`, `stockRecommnad`, `stockRecommned` 등의 표기를 표준 명칭인 **`stockRecommend`** 로 통일하여 정리하는 구현 계획입니다.

## User Review Required

> [!IMPORTANT]
> **전문가 검토 반영 핵심 안전 수칙**:
> 1. **프로세스 점유 해제 (Step 0)**: Windows 파일 잠금 방지를 위해 변경 전 백그라운드 Python/봇 프로세스 및 터미널 점유 해제 확인
> 2. **데이터 유실 0% 보장**: 구형 `stockRecommnad/result.md`와 `stockRecommned/result.md` 비교 검증 후 구형 폴더 정리
> 3. **Python `venv` 무결성 검증**: 폴더명 변경 후 `pytest` 실행을 통해 가상환경 인터프리터 작동 상태 점검

## 현황 분석 요약

| 대상 구분 | 현재 상태 | 변경 목표 |
| :--- | :--- | :--- |
| **메인 프로젝트 디렉터리** | `c:\Users\samsung\proj\stockRecommned` | `c:\Users\samsung\proj\stockRecommend` |
| **잔여/구형 디렉터리** | `c:\Users\samsung\proj\stockRecommnad` (`result.md`만 존재) | 최신 데이터 확인 후 안전하게 정리/통합 |
| **봇 및 환경설정** | `antigravity_bot.py`, `bot_config.json` 내 `stockRecommned` 경로 참조 | `stockRecommend` 경로로 갱신 |
| **마크다운 문서 (설계/가이드)** | `README.md`, `system_architecture.md`, `deployment.md`, `UI_DESIGN.md`, `telegram_bot_guide.md`, `screener_integration_qa_report.md` 내 `stockRecommnad` 링크 다수 | 모든 내부 파일 링크 및 설명 문구를 `stockRecommend`로 치환 |
| **실행 및 스크래치 스크립트** | `run_pipeline.bat`, `scratch/*.py` 내 로컬/원격 경로 하드코딩 | `c:\Users\samsung\proj\stockRecommend` 및 `/root/stockRecommend` 로 갱신 |

---

## Step-by-Step 실행 워크플로우

```mermaid
flowchart TD
    S0[Step 0: 사전 안전 검증<br>- 파일 핸들 점유 해제<br>- result.md 비교 검증] --> S1[Step 1: 문서 및 스크립트 내부 텍스트 일괄 치환<br>- README, design, manual, scratch, bat]
    S1 --> S2[Step 2: 외부 봇 및 설정 파일 갱신<br>- antigravity_bot.py, bot_config.json]
    S3[Step 3: 폴더명 변경 및 구형 폴더 정리<br>- stockRecommned -> stockRecommend<br>- stockRecommnad 정리]
    S2 --> S3
    S3 --> S4[Step 4: 가상환경(venv) 및 패키지 무결성 검증<br>- pyvenv.cfg 확인, pytest 실행]
    S4 --> S5[Step 5: QA 검증 및 최종 리포트<br>- 잔여 오타 0건 확인, Dry-run 검증]
```

---

## Proposed Changes

### Step 0: 사전 안전 검증 (Pre-Flight Safety Check)
- `stockRecommnad/result.md`와 `stockRecommned/result.md` 내용 무결성 비교
- 파이썬 프로세스 점유 상태 확인

### Step 1: 문서 및 스크립트 내부 텍스트 일괄 치환
- `README.md`: 프로젝트 트리 및 작업 스케줄러 경로 수정
- `design/*.md`: `system_architecture.md`, `deployment.md`, `UI_DESIGN.md`, `telegram_bot_guide.md` 등 모든 `file:///` 링크 및 본문 텍스트 수정
- `manual/telegram_bot_guide.md`: 실행 명령어 및 환경설정 링크 수정
- `run_pipeline.bat`: `PROJECT_DIR`을 `c:\Users\samsung\proj\stockRecommend`로 갱신
- `scratch/*.py`: 로컬(`stockRecommend`) 및 원격(`/root/stockRecommend`) 참조 경로 일괄 치환

### Step 2: 외부 봇 및 환경설정 갱신
- `antigravity_bot.py`: 기본 `active_project_path` 및 프로젝트 매칭 로직을 `stockRecommend`로 갱신
- `bot_config.json`: `active_project_path`를 `c:\Users\samsung\proj\stockRecommend`로 갱신

### Step 3: 디렉터리 이름 변경 및 잔여 폴더 정리
- `c:\Users\samsung\proj\stockRecommned` &rarr; `c:\Users\samsung\proj\stockRecommend`로 폴더명 변경
- `c:\Users\samsung\proj\stockRecommnad` 폴더 안전 정리

### Step 4: 가상환경(venv) 무결성 확인 및 테스트
- `stockRecommend/venv/Scripts/python.exe -m pytest tests/` 실행하여 테스트 전원 통과 확인
- `stockRecommend/venv/Scripts/python.exe main.py --dry-run` 실행 검증

### Step 5: QA 전수 조사 및 완료 리포트 작성
- 전체 프로젝트 파일 대상 정규식 `(stockrecomm|recommned|recommnad|stockrecommand)` 잔여 검색 0건 확인
- `walkthrough.md` 및 최종 완료 보고서 작성

---

## Verification Plan

### Automated Tests
- 폴더명 변경 후 가상환경에서 pytest 전체 테스트 실행:
  ```powershell
  cd c:\Users\samsung\proj\stockRecommend
  .\venv\Scripts\python.exe -m pytest tests/
  ```

### Manual Verification
1. **링크 유효성 검증**: 마크다운 파일 내 `file:///` 링크가 변경된 `stockRecommend` 경로로 올바르게 연결되는지 확인
2. **봇 실행 검증**: `c:\Users\samsung\proj\antigravity_bot.py` 실행 시 `stockRecommend` 프로젝트 경로를 정상적으로 로드하는지 확인
3. **전체 텍스트 잔여 검색**: `stockRecommnad`, `stockRecommned` 잔여 검색 시 의도치 않은 누락이 없는지 최종 점검
