# 🎓 전문가 패널 종합 검토 보고서 (Expert Plan Review)

본 보고서는 `stockrecommand` 표기를 `stockRecommend`로 일괄 변경·마이그레이션하는 계획에 대해, 프로젝트 R&R에 정의된 전문 에이전트(Core Developer, QA Engineer, DevOps Specialist, Technical Writer, Project Manager) 관점에서 다각도로 심층 검토한 결과입니다.

---

## 👥 1. 전문가별 상세 리뷰 의견

### 💻 1) Core Developer (핵심 개발자)
> **"Windows 환경의 디렉터리 잠금(File Lock) 및 파이썬 venv 참조 경로 유효성 확보가 핵심입니다."**

* **⚠️ 파일/프로세스 잠금 리스크**:
  * Windows OS 특성상 VS Code, 터미널, 백그라운드에서 실행 중인 `antigravity_bot.py` 또는 Python 인터프리터가 `stockRecommned` 폴더 내부 파일을 열고 있으면 `Rename-Item` 시 `PermissionError(Access is denied)`가 발생합니다.
  * **대응책**: 이름 변경 전 관련 백그라운드 프로세스 종료 및 파일 핸들 점유 해제 확인 절차를 계획 0단계에 명시.
* **⚠️ Python `venv` 경로 깨짐 방지**:
  * Windows 가상환경(`venv`)의 `pyvenv.cfg` 및 `venv/Scripts/*.bat`, `activate` 스크립트에는 기존 폴더의 절대 경로가 기록되어 있을 수 있습니다.
  * **대응책**: 폴더명 변경 후 `venv/pyvenv.cfg` 내의 `home` 및 base 경로를 확인하고, `venv/Scripts/python.exe -m pytest` 실행 테스트로 인터프리터 정상 작동을 검증. 필요 시 venv 재성성 스크립트 마련.

---

### 🧪 2) QA Engineer (품질 검증자)
> **"0% 데이터 유실 보장과 잔여 오타(Residual Typos) 제로화 검증이 필수입니다."**

* **⚠️ 구형 폴더(`stockRecommnad`) 데이터 보존성**:
  * `stockRecommnad`에 존재하는 `result.md`와 `stockRecommned/result.md`의 파일 해시(SHA256) 또는 내용을 사전에 비교 검증하여, 최신 데이터가 누락 없이 보존되는지 확정 후 구형 폴더를 정리해야 합니다.
* **⚠️ 정규식 기반 전수 검사**:
  * 단순 단어 검색이 아닌 대소문자 무시 정규식 `(stockrecomm|recommned|recommnad|stockrecommand)`을 이용해 `design/`, `manual/`, `app/`, `tests/`, `scratch/`, 루트 설정 파일 전수 검사를 실행하고 잔여 건수 0건을 확인해야 합니다.
* **⚠️ 회귀 테스트(Regression Test)**:
  * 이름 변경 후 `pytest tests/` 전체 패스 및 `python main.py --dry-run`이 정상적으로 로컬 리포트를 생성하는지 확인.

---

### 🚀 3) DevOps / Infra Specialist (인프라/배포 전문가)
> **"로컬 환경 변경이 원격 배포(Vercel, Cafe24 VPS, Task Scheduler)와 충돌하지 않도록 명명 규칙을 표준화해야 합니다."**

* **⚠️ 케이스별 명명 규칙(Naming Convention) 확립**:
  * **Windows 로컬 프로젝트 디렉터리 및 코드/문서**: `stockRecommend` (Pascal/CamelCase)
  * **원격 VPS Linux 디렉터리 및 서비스**: `/root/stockRecommend`, `stock-recommend.service` (kebab-case)
  * **Vercel 프로덕션 도메인**: `stockrecommend.vercel.app` (kebab-case)
* **⚠️ Windows Task Scheduler 갱신**:
  * `run_pipeline.bat` 내부 경로(`set PROJECT_DIR=c:\Users\samsung\proj\stockRecommend`) 수정과 더불어, 실제 윈도우 작업 스케줄러 등록 정보(`taskschd.msc`)의 작업 시작 위치도 `stockRecommend`로 갱신 안내 포함 필요.

---

### ✍️ 4) Technical Writer (테크니컬 라이터)
> **"문서 내 모든 링크의 일관성 및 파일 클릭 링크(file:///) 유효성을 완벽히 맞추어야 합니다."**

* **⚠️ 마크다운 링크 파손 방지**:
  * `README.md`, `system_architecture.md`, `UI_DESIGN.md`, `deployment.md`, `telegram_bot_guide.md` 내에 존재하는 `file:///c:/Users/samsung/proj/stockRecommnad/...` 형태의 절대 링크를 모두 `stockRecommend`로 일괄 교정.
* **⚠️ 용어 일관성**:
  * 문서 제목, 헤더, 아키텍처 다이어그램(Mermaid) 및 설명 텍스트에서 혼용된 `stockrecommand`, `stockRecommnad`, `stockRecommned`를 모두 `stockRecommend`로 통일.

---

## 📋 2. 최종 승인된 실행 단계 (개선된 Step-by-Step 워크플로우)

```mermaid
flowchart TD
    S0[Step 0: 사전 안전 검증<br>- 프로세스/핸들 점유 해제<br>- result.md 백업/비교] --> S1[Step 1: 문서 및 스크립트 내부 텍스트 일괄 치환<br>- README, design, manual, scratch, bat]
    S1 --> S2[Step 2: 외부 봇 및 설정 파일 갱신<br>- antigravity_bot.py, bot_config.json]
    S3[Step 3: 폴더명 변경 및 구형 폴더 정리<br>- stockRecommned -> stockRecommend<br>- stockRecommnad 정리]
    S2 --> S3
    S3 --> S4[Step 4: 가상환경(venv) 및 패키지 무결성 검증<br>- pyvenv.cfg 확인, pytest 실행]
    S4 --> S5[Step 5: QA 검증 및 최종 리포트<br>- 잔여 오타 0건 확인, Dry-run 검증]
```

---

## 🎯 3. 전문가 패널 종합 결론
> **"본 계획은 데이터 유실 위험이 없으며, Windows 환경의 특수성과 가상환경 의존성을 모두 고려한 안전한 마이그레이션 계획으로 판정되어 만장일치로 승인(Approved)합니다."**
