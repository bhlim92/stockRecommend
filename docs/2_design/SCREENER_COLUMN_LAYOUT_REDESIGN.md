# 📐 AI 종목 스크리너 테이블 칼럼 레이아웃 리밸런싱 및 '핵심 분석 근거' 가독성 개선 설계서

## 1. 📌 문제 현황 및 개선 배경

### 1.1 현상 분석
- **현상**: KOSPI 200 및 KOSDAQ 탭에서 스크리닝 결과를 조회할 때, 가장 우측에 위치한 **'핵심 분석 근거' 칼럼이 1글자 너비로 압축되어 세로로 길게 늘어지는 현상** 발생.
  ```text
  [현재 렌더링 상태]
  핵
  심
  분
  석
  근
  거
  ---
  단
  기
  골
  든
  크
  로
  스
  ...
  ```
- **원인 분석**:
  1. **고정 너비 칼럼들의 과도한 화면 점유**:
     - 기존 thead에서 앞선 9개 칼럼(순위, 티커, 섹터, 추천의견, 진입점수, 평가점수, 종합점수, 추이, 분석일시)에 고정된 픽셀 너비 합계만 **1,080px**에 달함.
     - 특히 단순 2자리 숫자가 들어가는 점수 칼럼(진입 130px, 평가 130px, 종합 120px)에 불필요하게 380px이 할당되어 공간을 낭비함.
  2. **'핵심 분석 근거' 칼럼의 너비 미지정 및 우선순위 밀림**:
     - `<th>핵심 분석 근거</th>`에 `width` 및 `min-width`가 전혀 지정되어 있지 않아, 브라우저의 기본 테이블 렌더링 엔진(`table-layout: auto`)이 앞선 고정 칼럼들을 먼저 배치한 후 남은 자투리 공간(10~30px)만 마지막 칼럼에 할당함.
  3. **한글 단어 분절(Wrap) 속성 결여**:
     - `word-break: keep-all` 및 `white-space: normal` 처리가 없어 좁은 너비에서 글자 단위로 강제 줄바꿈이 일어남.
  4. **테이블 자체의 최소 너비(min-width) 부재**:
     - 화면 해상도나 창 크기가 1400px 미만일 때 테이블이 무조건 화면 폭에 맞춰 찌그러지며 마지막 칼럼이 파괴됨.

---

## 2. 🎯 개선 목표

1. **불필요한 고정 칼럼 너비 다이어트**: 숫자/뱃지 칼럼의 여백을 240px 이상 회수.
2. **'핵심 분석 근거' 칼럼에 충분한 너비(최소 260px ~ 300px) 보장**:
   - 한글 문장이 2~3줄 내에서 단어 단위(`word-break: keep-all`)로 자연스럽게 읽히도록 배치.
3. **테이블 최소 너비(`min-width: 1250px`) 및 부드러운 가로 스크롤 적용**:
   - 해상도가 좁아져도 칼럼이 찌그러지지 않고 본연의 형태를 온전히 유지.
4. **KOSPI / KOSDAQ 한글 환경 최적화**:
   - 종목명과 티커, 섹터 태그가 한글 폰트에서 깔끔하게 정렬되도록 세부 패딩 및 정렬 튜닝.

---

## 3. 📊 칼럼 너비 리밸런싱 매트릭스 (Before vs After)

| 칼럼명 | 기존 너비 (As-Is) | 개선 너비 (To-Be) | 절감/증가 폭 | 사유 및 최적화 근거 |
| :--- | :---: | :---: | :---: | :--- |
| **순위** | 50px | **45px** | ▼ 5px | 1~200 번호 표시 (중앙 정렬) |
| **티커** | 90px | **85px** | ▼ 5px | 6자리 + 접미사 (005930.KS) 표시 충분 |
| **종목명** | 가변 (지정 없음) | **130px** (min) | - | 한글 6~8자 기준 줄바꿈 없는 크기 확보 |
| **섹터** | 110px | **95px** | ▼ 15px | 섹터 뱃지(최대 6글자)에 최적화 |
| **추천의견** | 110px | **85px** | ▼ 25px | '강력매수' 4글자 뱃지 너비에 최적화 |
| **진입 점수** | 130px | **80px** | ▼ 50px | 단순 숫자(`85/100`) 표시에 80px이면 여유 |
| **평가 점수** | 130px | **80px** | ▼ 50px | 단순 숫자(`78/100`) 표시에 80px이면 여유 |
| **종합 점수** | 120px | **75px** | ▼ 45px | 2자리 볼드 텍스트(`82`)에 75px이면 충분 |
| **최근 20일 추이** | 160px | **135px** | ▼ 25px | 스파크라인 SVG(100px) + 등락률 뱃지 수용 |
| **분석 일시** | 180px | **130px** | ▼ 50px | 날짜/시간 포맷(`09-09 06:05` or 11px)에 최적 |
| **핵심 분석 근거** | **가변 (압축 파괴)** | **가변 (min: 280px, 권장: 320px+)** | **▲ 265px+** | **회수한 265px을 몰아주어 정상 문장 표시 보장** |
| **합계** | - | **테이블 min-width: 1250px** | - | **화면 축소 시에도 칼럼 찌그러짐 원천 차단** |

---

## 4. 🛠️ 상세 CSS & HTML 설계

### 4.1 HTML thead 구조 개선 ([app/static/screener.html](file:///c:/Users/samsung/proj/stockRecommend/app/static/screener.html))

```html
<thead>
    <tr>
        <th class="hide-on-mobile col-rank" style="width: 45px; text-align: center;">순위</th>
        <th class="col-ticker" style="width: 85px;">티커</th>
        <th class="col-name" style="width: 130px;">종목명</th>
        <th class="hide-on-mobile sortable col-sector" data-col="sector" style="width: 95px; text-align: center;">섹터 <span id="sort-sector-indicator"></span></th>
        <th class="hide-on-mobile sortable col-rating" data-col="analyst_rating" style="width: 85px; text-align: center;">추천의견 <span id="sort-analyst_rating-indicator"></span></th>
        <th class="sortable hide-on-mobile col-score" data-col="entry_score" style="width: 80px; text-align: center;">진입 <span id="sort-entry_score-indicator"></span></th>
        <th class="sortable hide-on-mobile col-score" data-col="eval_score" style="width: 80px; text-align: center;">평가 <span id="sort-eval_score-indicator"></span></th>
        <th class="sortable col-total-score" data-col="total_score" style="width: 75px; text-align: center;">종합 <span id="sort-total_score-indicator"></span></th>
        <th class="hide-on-mobile sortable col-trend" data-col="trend_pct" style="width: 135px; text-align: center;">20일 추이 <span id="sort-trend_pct-indicator"></span></th>
        <th class="hide-on-mobile col-date" style="width: 130px; text-align: center;">분석 일시</th>
        <th class="col-rationale" style="min-width: 280px;">핵심 분석 근거</th>
    </tr>
</thead>
```

### 4.2 CSS 스타일 규칙 ([app/static/style.css](file:///c:/Users/samsung/proj/stockRecommend/app/static/style.css))

```css
/* Screener Holdings Table Container */
.table-container {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.holdings-table {
    width: 100%;
    min-width: 1250px; /* 칼럼 찌그러짐 방지 */
    border-collapse: collapse;
    table-layout: fixed; /* 예측 가능한 고정 칼럼 분배 */
}

/* 핵심 분석 근거 전용 셀 스타일 */
.holdings-table th.col-rationale {
    min-width: 280px;
}

.holdings-table td.col-rationale-cell {
    min-width: 280px;
    font-size: 0.84rem;
    line-height: 1.5;
    color: #e2e8f0;
    white-space: normal;
    word-break: keep-all; /* 단어 단위 줄바꿈으로 한글 가독성 극대화 */
    overflow-wrap: break-word;
    padding: 10px 14px;
}

/* 점수 및 헤더 폰트 간소화 */
.holdings-table th {
    padding: 10px 8px;
    white-space: nowrap;
}

.holdings-table td {
    padding: 10px 8px;
}
```

---

## 5. 🖥️ 화면 렌더링 목업 (Mockup)

```text
+----+-----------+---------------+--------+----------+------+------+------+----------------+--------------+----------------------------------------------+
|순위|   티커    |    종목명     |  섹터  | 추천의견 | 진입 | 평가 | 종합 |    20일 추이   |  분석 일시   |                 핵심 분석 근거               |
+----+-----------+---------------+--------+----------+------+------+------+----------------+--------------+----------------------------------------------+
| 1  | 005930.KS | 삼성전자      | IT기술 | 강력매수 |  85  |  78  |  82  | [==^==] +3.4%  | 09-09 06:05  | 단기 골든크로스 및 추세 상승 반전 발생,       |
|    |           |               |        |          |      |      |      |                |              | 외국인/기관 수급 동반 유입 (실적 턴어라운드) |
+----+-----------+---------------+--------+----------+------+------+------+----------------+--------------+----------------------------------------------+
| 2  | 000660.KS | SK하이닉스    | 반도체 |   매수   |  88  |  74  |  81  | [==^==] +5.1%  | 09-09 06:05  | HBM3E 공급 확대 및 신고가 갱신 모멘텀 지속   |
+----+-----------+---------------+--------+----------+------+------+------+----------------+--------------+----------------------------------------------+
```

---

## 6. 🚀 구현 및 검증 계획

1. **1단계**: [app/static/style.css](file:///c:/Users/samsung/proj/stockRecommend/app/static/style.css)에 `.col-rationale-cell` 및 `table-layout: fixed`, `min-width: 1250px` 스타일 추가.
2. **2단계**: [app/static/screener.html](file:///c:/Users/samsung/proj/stockRecommend/app/static/screener.html)의 `<thead>` 및 `renderTable()` 내의 `<td>` 클래스 적용.
3. **3단계**: Playwright를 이용해 KOSPI 200 탭 브라우저 렌더링 스크린샷 캡처 및 '핵심 분석 근거'가 정상적인 문장 단락으로 넓게 출력되는지 검증.
4. **4단계**: cafe24 원격 서버 및 GitHub 저장소 동기화 배포.
