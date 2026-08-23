/* ==============================================================================
   Quantum Dashboard Core JavaScript - Stock Recommendation System
   ============================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // API Endpoints
    const API_STATUS = "/api/status";
    const API_RUN = "/api/run";
    const API_PORTFOLIO = "/api/portfolio";
    const API_REPORTS = "/api/reports";
    const API_PIPELINE_INGEST = "/api/pipeline/ingest";
    const API_PIPELINE_NEWS = "/api/pipeline/news";
    const API_PIPELINE_YOUTUBE = "/api/pipeline/youtube";
    const API_PIPELINE_RECOMMENDING = "/api/pipeline/recommending";
    const API_PIPELINE_UPLOAD = "/api/pipeline/upload";
    const API_PORTFOLIO_GSPREAD = "/api/portfolio/gspread";
    const API_PORTFOLIO_REBALANCE = "/api/portfolio/rebalance";

    // DOM Elements
    const serverStatusBadge = document.getElementById("server-status-badge");
    const btnRunPipeline = document.getElementById("btn-run-pipeline");
    const btnLoader = btnRunPipeline.querySelector(".btn-loader");
    const btnText = btnRunPipeline.querySelector(".btn-text");
    
    const currentStepText = document.getElementById("current-step-text");
    const progressPercentText = document.getElementById("progress-percent-text");
    const progressBarFill = document.getElementById("progress-bar-fill");
    const logTerminal = document.getElementById("log-terminal");
    
    // Gemini settings inputs (In settings modal)
    const selectGeminiModel = document.getElementById("select-gemini-model");
    const inputGeminiApiKey = document.getElementById("input-gemini-api-key");
    const portfolioForm = document.getElementById("portfolio-form");

    // Modal elements
    const modalSettings = document.getElementById("modal-settings");
    const btnOpenSettings = document.getElementById("btn-open-settings");
    const btnCloseSettings = document.getElementById("btn-close-settings");
    const btnCancelSettings = document.getElementById("btn-cancel-settings");
    const btnSaveSettings = document.getElementById("btn-save-settings");

    const modalTerminal = document.getElementById("modal-terminal");
    const btnOpenTerminal = document.getElementById("btn-open-terminal");
    const btnCloseTerminal = document.getElementById("btn-close-terminal");
    const btnHideTerminal = document.getElementById("btn-hide-terminal");
    const btnClearTerminal = document.getElementById("btn-clear-terminal");

    // Reports list and viewer
    const reportsList = document.getElementById("reports-list");
    const reportViewerSection = document.getElementById("report-viewer-section");
    const viewingReportTitle = document.getElementById("viewing-report-title");
    const reportMdDisplay = document.getElementById("report-md-display");
    const btnCloseViewer = document.getElementById("btn-close-viewer");
    const holdingsList = document.getElementById("holdings-list");
    const btnGenerateRebalance = document.getElementById("btn-generate-rebalance");
    const rebalanceStrategyDisplay = document.getElementById("rebalance-strategy-display");
    const rebalanceCardsContainer = document.getElementById("rebalance-cards-container");

    // Step items map
    const stepItems = {
        "ingesting": document.getElementById("step-ingesting"),
        "news": document.getElementById("step-news"),
        "youtube": document.getElementById("step-youtube"),
        "recommending": document.getElementById("step-recommending"),
        "uploading": document.getElementById("step-uploading")
    };

    // DOM Elements for Caveats
    const caveatsPanel = document.getElementById("caveats-panel");
    const caveatsText = document.getElementById("caveats-text");

    // Caveats text for each phase
    const stepCaveats = {
        "idle": "자동 분석이 대기 중입니다. '지금 분석 시작하기' 버튼을 눌러 실시간 분석을 진행하십시오.",
        "ingesting": "<strong>[금융 데이터 수집]</strong> FRED 프록시를 통해 간접 조회하므로 실제 발표 시간과 수 시간의 오차가 존재할 수 있습니다.",
        "news": "<strong>[마켓 뉴스 분석]</strong> Yahoo Finance 및 Google News RSS 검색 결과를 중복 필터링하여 주요 키워드로 요약합니다.",
        "youtube": "<strong>[유튜브 전문가 요약]</strong> 최근 48시간 내의 영상만 분석하며 한글/영어 자막을 추출하여 핵심 키포인트를 LLM으로 정리합니다.",
        "screening": "<strong>[CANSLIM 조건 스크리닝]</strong> C, A, N, S, L, I, M 요소를 계량적으로 분석하여 진입 및 평가 점수를 계산합니다.",
        "rebalancing": "<strong>[포트폴리오 리밸런싱]</strong> 자산 배분 비중 괴리율(Drift)이 5% 이상 벌어졌을 때만 거래 제안(Rebalance Action)이 활성화됩니다.",
        "recommending": "<strong>[AI 추천 보고서 생성]</strong> 수집된 데이터셋을 바탕으로 Google Gemini가 종합 리포트를 합성합니다.",
        "uploading": "<strong>[구글 드라이브 업로드]</strong> 생성된 마크다운 리포트는 Google Docs 문서로 변환되어 클라우드에 자동 업로드됩니다.",
        "done": "<strong>[분석 완료]</strong> 일일 분석 파이프라인이 안전하게 완료되었습니다.",
        "failed": "<strong>[오류 발생]</strong> 분석 수행 중 예외가 발생했습니다. 로그 터미널 창을 열어 에러를 확인하십시오."
    };

    // Tracking states & charts
    let isPipelineRunning = false;
    let statusInterval = null;
    let lastRenderedLogsCount = 0;
    let portfolioSettings = null;
    let portfolioHoldings = null;
    let currentSortKey = "account_type";
    let currentSortOrder = "asc";
    let exchangeRateUSD = 1380.0;
    let pieChart = null;
    let compareChart = null;

    // Initialize UI
    inputGeminiApiKey.value = localStorage.getItem("gemini_api_key") || "";
    checkApiKeyWarning();
    loadPortfolio();
    loadReportsList();
    loadGspreadPortfolio();
    loadRebalanceStrategy();
    startPollingStatus();
    loadMacroIndicators();
    loadInvestmentOpinions();

    // Sortable headers click listeners
    const sortableHeaders = document.querySelectorAll("#holdings-table th.sortable");
    sortableHeaders.forEach(th => {
        th.addEventListener("click", () => {
            const key = th.getAttribute("data-sort");
            if (key) {
                sortHoldings(key);
            }
        });
    });

    function checkApiKeyWarning() {
        const apiKey = localStorage.getItem("gemini_api_key") || "";
        const warningBanner = document.getElementById("warning-api-key");
        if (warningBanner) {
            if (!apiKey) {
                warningBanner.classList.remove("hidden");
            } else {
                warningBanner.classList.add("hidden");
            }
        }
    }

    const btnWarningSetup = document.getElementById("btn-warning-setup");
    if (btnWarningSetup) {
        btnWarningSetup.addEventListener("click", () => {
            btnOpenSettings.click();
        });
    }

    // Logout DOM element
    const btnLogout = document.getElementById("btn-logout");

    // Modal: Settings Event Listeners
    btnOpenSettings.addEventListener("click", () => {
        if (portfolioSettings) {
            selectGeminiModel.value = portfolioSettings.gemini_model || "gemini-2.5-flash";
        }
        inputGeminiApiKey.value = localStorage.getItem("gemini_api_key") || "";
        modalSettings.classList.add("active");
    });
    const hideSettingsModal = () => modalSettings.classList.remove("active");
    btnCloseSettings.addEventListener("click", hideSettingsModal);
    btnCancelSettings.addEventListener("click", hideSettingsModal);
    btnSaveSettings.addEventListener("click", (e) => {
        savePortfolio(e);
        hideSettingsModal();
    });

    // Close settings modal when clicking overlay backdrop
    modalSettings.addEventListener("click", (e) => {
        if (e.target === modalSettings) {
            hideSettingsModal();
        }
    });

    // Modal: Log Terminal Event Listeners
    btnOpenTerminal.addEventListener("click", () => {
        modalTerminal.classList.add("active");
    });
    const hideTerminalModal = () => modalTerminal.classList.remove("active");
    btnCloseTerminal.addEventListener("click", hideTerminalModal);
    btnHideTerminal.addEventListener("click", hideTerminalModal);
    btnClearTerminal.addEventListener("click", () => {
        logTerminal.innerHTML = '<div class="terminal-line system-line">[SYSTEM] 로그가 비워졌습니다.</div>';
        lastRenderedLogsCount = 0;
    });

    // Close terminal modal when clicking overlay backdrop
    modalTerminal.addEventListener("click", (e) => {
        if (e.target === modalTerminal) {
            hideTerminalModal();
        }
    });

    // Close modals on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            hideSettingsModal();
            hideTerminalModal();
            if (typeof window.closeChartModal === "function") {
                window.closeChartModal();
            }
        }
    });

    // Event Listeners for running pipeline and rebalance
    btnRunPipeline.addEventListener("click", triggerPipelineRun);
    portfolioForm.addEventListener("submit", savePortfolio);
    btnCloseViewer.addEventListener("click", () => {
        reportViewerSection.classList.add("hidden");
    });
    if (btnGenerateRebalance) {
        btnGenerateRebalance.addEventListener("click", generateRebalanceStrategy);
    }
    if (btnLogout) {
        btnLogout.addEventListener("click", () => {
            fetch("/api/auth/logout", { method: "POST" })
                .then(() => {
                    window.location.href = "/login.html";
                })
                .catch(err => {
                    console.error("Logout failed:", err);
                    window.location.href = "/login.html";
                });
        });
    }

    // ==========================================================================
    // Core Functions & Polling
    // ==========================================================================

    function startPollingStatus() {
        if (statusInterval) clearInterval(statusInterval);
        fetchStatus();
        statusInterval = setInterval(fetchStatus, 1500);
    }

    async function fetchStatus() {
        if (isPipelineRunning) return;
        try {
            const response = await fetch(`${API_STATUS}?_t=${Date.now()}`);
            if (isPipelineRunning) return;
            if (!response.ok) throw new Error("Status query failed");
            
            const data = await response.json();
            if (isPipelineRunning) return;
            updatePipelineUI(data);
        } catch (error) {
            if (isPipelineRunning) return;
            console.error("Error polling system status:", error);
        }
    }

    function updatePipelineUI(data) {
        const { status, progress, current_step, logs, error } = data;
        
        serverStatusBadge.className = "status-badge";
        if (status === "idle") {
            serverStatusBadge.classList.add("status-idle");
            serverStatusBadge.innerText = "대기중 (IDLE)";
            isPipelineRunning = false;
        } else if (status === "done") {
            serverStatusBadge.classList.add("status-done");
            serverStatusBadge.innerText = "완료 (SUCCESS)";
            isPipelineRunning = false;
        } else if (status === "failed") {
            serverStatusBadge.classList.add("status-failed");
            serverStatusBadge.innerText = "실패 (FAILED)";
            isPipelineRunning = false;
        } else {
            serverStatusBadge.classList.add("status-running");
            serverStatusBadge.innerText = `진행중 (${status.toUpperCase()})`;
            isPipelineRunning = true;
        }

        if (isPipelineRunning) {
            btnRunPipeline.disabled = true;
            btnLoader.classList.remove("hidden");
            btnText.innerText = "분석 진행 중...";
        } else {
            btnRunPipeline.disabled = false;
            btnLoader.classList.add("hidden");
            btnText.innerText = "지금 분석 시작하기 (ON-DEMAND)";
        }

        currentStepText.innerText = current_step;
        progressPercentText.innerText = `${progress}%`;
        progressBarFill.style.width = `${progress}%`;

        Object.keys(stepItems).forEach(key => {
            const item = stepItems[key];
            if (!item) return;

            item.className = "step-item";
            
            if (status === key) {
                item.classList.add("active");
            } else {
                const stepsSeq = ["ingesting", "news", "youtube", "recommending", "uploading", "done"];
                const currentIdx = stepsSeq.indexOf(status);
                const stepIdx = stepsSeq.indexOf(key);
                
                if (status === "done" || (currentIdx > stepIdx && currentIdx !== -1)) {
                    item.classList.add("completed");
                }
            }
        });

        if (caveatsText && caveatsPanel) {
            const caveatContent = stepCaveats[status] || stepCaveats["idle"];
            caveatsText.innerHTML = caveatContent;
            
            if (status !== "idle" && status !== "done" && status !== "failed") {
                caveatsPanel.classList.add("highlight");
            } else {
                caveatsPanel.classList.remove("highlight");
            }
        }

        if (logs.length > lastRenderedLogsCount) {
            for (let i = lastRenderedLogsCount; i < logs.length; i++) {
                const line = logs[i];
                let type = "";
                if (line.includes("WARNING")) type = "warning-line";
                else if (line.includes("ERROR")) type = "error-line";
                else if (line.includes("SUCCESS") || line.includes("successfully")) type = "success-line";
                
                addTerminalLine(line, type);
            }
            lastRenderedLogsCount = logs.length;
        }

        if (status === "ingesting" && progress <= 5) {
            logTerminal.innerHTML = "";
            lastRenderedLogsCount = 0;
            addTerminalLine("[SYSTEM] 새로운 분석 파이프라인이 시작되었습니다.");
        }

        if (status === "done" && progress === 100 && lastRenderedLogsCount > 0) {
            loadReportsList();
            lastRenderedLogsCount = 0;
        }
    }

    function addTerminalLine(text, className = "") {
        const lineDiv = document.createElement("div");
        lineDiv.className = "terminal-line";
        if (className) lineDiv.classList.add(className);
        lineDiv.innerText = text;
        logTerminal.appendChild(lineDiv);
        logTerminal.scrollTop = logTerminal.scrollHeight;
    }

    function updateClientStepUI(status, progress, currentStepName) {
        serverStatusBadge.className = "status-badge status-running";
        serverStatusBadge.innerText = `진행중 (${status.toUpperCase()})`;
        
        btnRunPipeline.disabled = true;
        btnLoader.classList.remove("hidden");
        btnText.innerText = "분석 진행 중...";
        
        currentStepText.innerText = currentStepName;
        progressPercentText.innerText = `${progress}%`;
        progressBarFill.style.width = `${progress}%`;
        
        Object.keys(stepItems).forEach(key => {
            const item = stepItems[key];
            if (!item) return;
            item.className = "step-item";
            
            const stepsSeq = ["ingesting", "news", "youtube", "recommending", "uploading", "done"];
            const currentIdx = stepsSeq.indexOf(status);
            const stepIdx = stepsSeq.indexOf(key);
            
            if (status === key) {
                item.classList.add("active");
            } else if (currentIdx > stepIdx && currentIdx !== -1) {
                item.classList.add("completed");
            }
        });
        
        if (caveatsText && caveatsPanel) {
            caveatsText.innerHTML = stepCaveats[status] || stepCaveats["idle"];
            caveatsPanel.classList.add("highlight");
        }
    }

    function markPipelineDone() {
        serverStatusBadge.className = "status-badge status-done";
        serverStatusBadge.innerText = "완료 (SUCCESS)";
        btnRunPipeline.disabled = false;
        btnLoader.classList.add("hidden");
        btnText.innerText = "지금 분석 시작하기 (ON-DEMAND)";
        
        currentStepText.innerText = "분석 완료";
        progressPercentText.innerText = "100%";
        progressBarFill.style.width = "100%";
        
        Object.keys(stepItems).forEach(key => {
            const item = stepItems[key];
            if (item) {
                item.className = "step-item completed";
            }
        });
        
        if (caveatsText && caveatsPanel) {
            caveatsText.innerHTML = stepCaveats["done"];
            caveatsPanel.classList.remove("highlight");
        }
        
        isPipelineRunning = false;
        startPollingStatus();
    }

    function markPipelineFailed(errorMsg) {
        serverStatusBadge.className = "status-badge status-failed";
        serverStatusBadge.innerText = "실패 (FAILED)";
        btnRunPipeline.disabled = false;
        btnLoader.classList.add("hidden");
        btnText.innerText = "지금 분석 시작하기 (ON-DEMAND)";
        
        currentStepText.innerText = "오류 발생";
        
        if (caveatsText && caveatsPanel) {
            caveatsText.innerHTML = stepCaveats["failed"];
            caveatsPanel.classList.remove("highlight");
        }
        
        addTerminalLine(`[SYSTEM ERROR] 파이프라인 수행 실패: ${errorMsg}`, "error-line");
        isPipelineRunning = false;
        startPollingStatus();
    }

    function appendStepLogs(logs) {
        if (logs && Array.isArray(logs)) {
            logs.forEach(line => {
                let type = "";
                if (line.includes("WARNING")) type = "warning-line";
                else if (line.includes("ERROR")) type = "error-line";
                else if (line.includes("SUCCESS") || line.includes("successfully")) type = "success-line";
                addTerminalLine(line, type);
            });
        }
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async function startCooldown(seconds, reason) {
        const timerBox = document.getElementById("cooldown-timer-box");
        const timerSeconds = document.getElementById("cooldown-timer-seconds");
        const timerBar = document.getElementById("cooldown-timer-bar");
        
        if (timerBox) {
            timerBox.classList.remove("hidden");
            timerBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        
        const total = seconds;
        for (let i = seconds; i >= 0; i--) {
            if (timerSeconds) timerSeconds.innerText = `${i}초 남음`;
            if (timerBar) {
                const pct = (i / total) * 100;
                timerBar.style.width = `${pct}%`;
            }
            addTerminalLine(`[SYSTEM] ${reason}을 위해 대기 중... (${i}초 남음)`);
            if (i > 0) {
                await delay(1000);
            }
        }
        
        if (timerBox) {
            timerBox.classList.add("hidden");
        }
    }

    function saveReportToLocalStorage(filename, markdown) {
        let archive = [];
        try {
            archive = JSON.parse(localStorage.getItem("reports_archive")) || [];
        } catch (e) {
            archive = [];
        }
        archive = archive.filter(item => item.filename !== filename);
        archive.unshift({ filename, content: markdown });
        localStorage.setItem("reports_archive", JSON.stringify(archive));
    }

    async function triggerPipelineRun() {
        if (isPipelineRunning) return;
        
        const apiKey = inputGeminiApiKey ? inputGeminiApiKey.value.trim() : "";
        if (!apiKey) {
            btnOpenSettings.click();
            setTimeout(() => {
                inputGeminiApiKey.focus();
            }, 300);
            addTerminalLine("[SYSTEM ERROR] Gemini API Key가 제공되지 않아 분석을 시작할 수 없습니다. 설정을 완료해 주십시오.", "error-line");
            return;
        }

        localStorage.setItem("gemini_api_key", apiKey);

        isPipelineRunning = true;
        if (statusInterval) clearInterval(statusInterval);
        logTerminal.innerHTML = "";
        lastRenderedLogsCount = 0;
        
        Object.keys(stepItems).forEach(key => {
            if (stepItems[key]) stepItems[key].className = "step-item";
        });
        
        addTerminalLine("[SYSTEM] 클라이언트 사이드 순차 분석 파이프라인을 기동합니다...");
        
        let marketData = null;
        let newsData = null;
        let youtubeSummaries = null;
        let reportMarkdown = null;
        let gdocLink = "";

        const selectedModel = selectGeminiModel ? selectGeminiModel.value : "gemini-2.5-flash";

        try {
            // Step 1: Ingest
            updateClientStepUI("ingesting", 10, "금융 데이터 수집 중...");
            addTerminalLine("[SYSTEM] 1단계: 금융 데이터 수집 요청 중...");
            let res = await fetch(API_PIPELINE_INGEST, { method: "POST" });
            if (!res.ok) throw new Error(`1단계 수집 실패 (HTTP ${res.status})`);
            let data = await res.json();
            marketData = data.market_data;
            appendStepLogs(data.logs);
            
            // Step 2: News
            updateClientStepUI("news", 30, "마켓 뉴스 분석 중...");
            addTerminalLine("[SYSTEM] 2단계: 마켓 주요 뉴스 분석 요청 중...");
            res = await fetch(API_PIPELINE_NEWS, { method: "POST" });
            if (!res.ok) throw new Error(`2단계 뉴스 분석 실패 (HTTP ${res.status})`);
            data = await res.json();
            newsData = data.news;
            appendStepLogs(data.logs);
            
            // Wait 13 seconds (Gemini API Cooldown)
            updateClientStepUI("news", 45, "대기 지연 실행 중...");
            await startCooldown(13, "유튜브 분석 전 API 호출 속도 제한(Rate Limit)");

            // Step 3: YouTube Summarizer
            updateClientStepUI("youtube", 60, "유튜브 전문가 요약 중...");
            addTerminalLine("[SYSTEM] 3단계: 유튜브 전문가 요약 요청 중...");
            res = await fetch(API_PIPELINE_YOUTUBE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: apiKey, model: selectedModel })
            });
            if (!res.ok) throw new Error(`3단계 유튜브 분석 실패 (HTTP ${res.status})`);
            data = await res.json();
            youtubeSummaries = data.youtube_summaries;
            appendStepLogs(data.logs);

            // Wait 13 seconds (Gemini API Cooldown)
            updateClientStepUI("youtube", 75, "대기 지연 실행 중...");
            await startCooldown(13, "보고서 합성 전 API 호출 속도 제한(Rate Limit)");

            // Step 4: Recommending
            updateClientStepUI("recommending", 85, "최종 추천 보고서 작성 중...");
            addTerminalLine("[SYSTEM] 4단계: AI 추천 보고서 생성 요청 중...");
            res = await fetch(API_PIPELINE_RECOMMENDING, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    api_key: apiKey,
                    model: selectedModel,
                    market_data: marketData,
                    news: newsData,
                    youtube_summaries: youtubeSummaries
                })
            });
            if (!res.ok) throw new Error(`4단계 보고서 생성 실패 (HTTP ${res.status})`);
            data = await res.json();
            reportMarkdown = data.report_markdown;
            appendStepLogs(data.logs);

            // Step 5: Upload
            updateClientStepUI("uploading", 95, "드라이브 업로드 및 저장 중...");
            addTerminalLine("[SYSTEM] 5단계: 아카이빙 및 업로드 요청 중...");
            res = await fetch(API_PIPELINE_UPLOAD, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ report_markdown: reportMarkdown })
            });
            if (!res.ok) throw new Error(`5단계 저장/업로드 실패 (HTTP ${res.status})`);
            data = await res.json();
            gdocLink = data.gdoc_link;
            appendStepLogs(data.logs);

            const timestamp = new Date().toISOString().split('T')[0];
            const reportFilename = `${timestamp}_report.md`;
            saveReportToLocalStorage(reportFilename, reportMarkdown);

            markPipelineDone();
            addTerminalLine(`[SUCCESS] 전체 파이프라인 분석이 성공적으로 종료되었습니다!`, "success-line");
            if (gdocLink) {
                addTerminalLine(`[SUCCESS] 구글 드라이브 업로드 주소: ${gdocLink}`, "success-line");
            }
            
            loadReportsList();
            renderReportInViewer(reportFilename, reportMarkdown);

        } catch (error) {
            console.error("Pipeline run failed:", error);
            markPipelineFailed(error.message);
        }
    }

    // ==========================================================================
    // Macro Indicators Loader
    // ==========================================================================

    async function loadMacroIndicators() {
        const kospiEl = document.getElementById("macro-kospi");
        const sp500El = document.getElementById("macro-sp500");
        const exRateEl = document.getElementById("macro-exchange-rate");
        const fngScoreEl = document.getElementById("macro-fng-score");
        const fngRatingEl = document.getElementById("macro-fng-rating");

        // 1. Fetch USD/KRW exchange rate from public endpoint
        try {
            const res = await fetch("https://open.er-api.com/v6/latest/USD");
            if (res.ok) {
                const data = await res.json();
                if (data && data.rates && data.rates.KRW) {
                    exchangeRateUSD = data.rates.KRW;
                    exRateEl.innerText = `${Math.round(exchangeRateUSD).toLocaleString('ko-KR')} KRW`;
                    tryRenderCharts(); // Trigger chart update if holdings loaded
                }
            }
        } catch (e) {
            console.warn("Failed to load exchange rate from open API:", e);
            exRateEl.innerText = "1,385 KRW (지연)";
        }

        // 2. Fetch live KOSPI & S&P 500 index values from backend API
        try {
            const res = await fetch(`/api/macro/indices?_t=${Date.now()}`);
            if (res.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (res.ok) {
                const data = await res.json();
                
                // Render KOSPI
                if (kospiEl && data.kospi) {
                    const k = data.kospi;
                    const sign = k.change >= 0 ? "▲" : "▼";
                    const color = k.change >= 0 ? "var(--accent-green)" : "#ff4d4d";
                    kospiEl.innerHTML = `${k.value.toLocaleString('ko-KR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} <span style="color: ${color}; font-size: 11px;">${sign} ${Math.abs(k.pct_change).toFixed(2)}%</span>`;
                }
                
                // Render S&P 500
                if (sp500El && data.sp500) {
                    const s = data.sp500;
                    const sign = s.change >= 0 ? "▲" : "▼";
                    const color = s.change >= 0 ? "var(--accent-green)" : "#ff4d4d";
                    sp500El.innerHTML = `${s.value.toLocaleString('ko-KR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} <span style="color: ${color}; font-size: 11px;">${sign} ${Math.abs(s.pct_change).toFixed(2)}%</span>`;
                }

                // Render Fear & Greed Index
                if (fngScoreEl && fngRatingEl && data.fear_greed) {
                    const fg = data.fear_greed;
                    fngScoreEl.innerText = fg.score;
                    fngRatingEl.innerText = fg.rating.replace("_", " ").toUpperCase();
                    
                    let ratingColor = "var(--text-muted)";
                    let ratingBg = "rgba(255, 255, 255, 0.06)";
                    const lowerRating = fg.rating.toLowerCase();
                    if (lowerRating.includes("extreme greed")) {
                        ratingColor = "#00ff88";
                        ratingBg = "rgba(0, 255, 136, 0.12)";
                    } else if (lowerRating.includes("greed")) {
                        ratingColor = "#a3ff00";
                        ratingBg = "rgba(163, 255, 0, 0.12)";
                    } else if (lowerRating.includes("extreme fear")) {
                        ratingColor = "#ff3333";
                        ratingBg = "rgba(255, 51, 51, 0.12)";
                    } else if (lowerRating.includes("fear")) {
                        ratingColor = "#ff8833";
                        ratingBg = "rgba(255, 136, 51, 0.12)";
                    } else { // neutral
                        ratingColor = "#ffcc00";
                        ratingBg = "rgba(255, 204, 0, 0.12)";
                    }
                    fngRatingEl.style.color = ratingColor;
                    fngRatingEl.style.backgroundColor = ratingBg;
                }
            }
        } catch (e) {
            console.error("Failed to load macro indices from backend:", e);
            // Fallback to static realistic values if API fails
            if (kospiEl) kospiEl.innerHTML = `2,668.21 <span style="color: var(--accent-green); font-size: 11px;">▲ 0.82%</span>`;
            if (sp500El) sp500El.innerHTML = `5,283.40 <span style="color: var(--accent-green); font-size: 11px;">▲ 1.15%</span>`;
            if (fngScoreEl) fngScoreEl.innerText = "50";
            if (fngRatingEl) {
                fngRatingEl.innerText = "NEUTRAL";
                fngRatingEl.style.color = "#ffcc00";
                fngRatingEl.style.backgroundColor = "rgba(255, 204, 0, 0.12)";
            }
        }
    }

    async function loadInvestmentOpinions() {
        const tableBody = document.getElementById("opinions-table-body");
        if (!tableBody) return;
        
        try {
            const res = await fetch(`/api/macro/opinions?_t=${Date.now()}`);
            if (res.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (res.ok) {
                const opinions = await res.json();
                tableBody.innerHTML = "";
                opinions.forEach(op => {
                    const row = document.createElement("tr");
                    row.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
                    
                    // Style rating colors
                    let color = "var(--text-secondary)";
                    let fontWeight = "normal";
                    const rating = op.opinion;
                    if (rating === "강력매수") {
                        color = "#00ff88";
                        fontWeight = "bold";
                    } else if (rating === "매수") {
                        color = "#a3ff00";
                        fontWeight = "600";
                    } else if (rating === "강력매도") {
                        color = "#ff3333";
                        fontWeight = "bold";
                    } else if (rating === "매도") {
                        color = "#ff8833";
                        fontWeight = "600";
                    } else { // 유지
                        color = "#ffcc00";
                        fontWeight = "normal";
                    }
                    
                    row.innerHTML = `
                        <td style="padding: 10px 8px; font-weight: 600;">${op.name}</td>
                        <td style="padding: 10px 8px; color: var(--text-muted); font-family: monospace; font-size: 10px;">${op.index}</td>
                        <td style="padding: 10px 8px; text-align: right; font-family: 'Orbitron', monospace;">${op.value.toLocaleString('ko-KR', {maximumFractionDigits: 2})}</td>
                        <td style="padding: 10px 8px; text-align: center;">
                            <span style="color: ${color}; font-weight: ${fontWeight};">${rating}</span>
                        </td>
                        <td style="padding: 10px 8px; line-height: 1.4; color: var(--text-muted);">${op.reason}</td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">투자 의견을 불러오는데 실패했습니다.</td></tr>`;
            }
        } catch (e) {
            console.error("Failed to load investment opinions:", e);
            tableBody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">오류: ${e.message}</td></tr>`;
        }

    }

    // ==========================================================================
    // Portfolio Settings & Databases
    // ==========================================================================

    async function loadPortfolio() {
        const savedSettings = localStorage.getItem("portfolio_settings");
        if (savedSettings) {
            try {
                portfolioSettings = JSON.parse(savedSettings);
                populatePortfolioUI(portfolioSettings);
                addTerminalLine("[SYSTEM] 브라우저 로컬 저장소에서 설정을 불러왔습니다.");
                tryRenderCharts();
                return;
            } catch (e) {
                console.error("Failed to parse local portfolio settings:", e);
            }
        }

        try {
            const response = await fetch(`${API_PORTFOLIO}?_t=${Date.now()}`);
            if (response.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (!response.ok) throw new Error("Portfolio load failed");
            
            portfolioSettings = await response.json();
            localStorage.setItem("portfolio_settings", JSON.stringify(portfolioSettings));
            populatePortfolioUI(portfolioSettings);
            tryRenderCharts();
        } catch (error) {
            console.error("Failed to load settings database:", error);
            addTerminalLine(`[SYSTEM ERROR] 설정을 불러오지 못했습니다: ${error.message}`, "error-line");
        }
    }

    function populatePortfolioUI(data) {
        if (selectGeminiModel && data) {
            selectGeminiModel.value = data.gemini_model || "gemini-2.5-flash";
        }
    }

    async function savePortfolio(e) {
        e.preventDefault();

        const apiKey = inputGeminiApiKey.value.trim();
        localStorage.setItem("gemini_api_key", apiKey);
        checkApiKeyWarning();

        const selectedModel = selectGeminiModel.value;
        const updatedData = {
            ...(portfolioSettings || {}),
            gemini_model: selectedModel
        };

        portfolioSettings = updatedData;
        localStorage.setItem("portfolio_settings", JSON.stringify(updatedData));

        try {
            const response = await fetch(API_PORTFOLIO, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(updatedData)
            });
            if (response.ok) {
                addTerminalLine("[SYSTEM] 모델 및 설정이 서버에도 저장되었습니다.", "success-line");
            }
        } catch (error) {
            console.warn("Backend settings save failed (normal for serverless/read-only fs):", error);
        }

        addTerminalLine("[SYSTEM] 설정이 브라우저에 저장되었습니다.", "success-line");
        loadPortfolio();
    }

    // ==========================================================================
    // Google Spreadsheet Portfolio holdings Functions & Chart.js
    // ==========================================================================

    async function loadGspreadPortfolio() {
        if (!holdingsList) return;
        
        holdingsList.innerHTML = `
            <tr class="skeleton-row">
                <td><span class="skeleton-placeholder" style="width: 45px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 50px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 120px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 70px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 70px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 90px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 90px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 80px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 50px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
            </tr>
            <tr class="skeleton-row">
                <td><span class="skeleton-placeholder" style="width: 45px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 60px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 100px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 70px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 70px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 90px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 90px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 80px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 50px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
                <td><span class="skeleton-placeholder" style="width: 40px;"></span></td>
            </tr>
        `;
        
        try {
            const response = await fetch(`${API_PORTFOLIO_GSPREAD}?_t=${Date.now()}`);
            if (response.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (!response.ok) throw new Error("API response not OK");
            
            const data = await response.json();
            portfolioHoldings = data;
            
            if (currentSortKey) {
                const targetKey = currentSortKey;
                const desiredOrder = currentSortOrder;
                currentSortKey = ""; // Reset to force no-toggle in next call
                sortHoldings(targetKey);
                if (currentSortOrder !== desiredOrder) {
                    sortHoldings(targetKey); // Toggle again to match original order
                }
            } else {
                await renderGspreadPortfolio(data);
            }
            tryRenderCharts();
        } catch (error) {
            console.error("Failed to load Google Sheet holdings:", error);
            holdingsList.innerHTML = `<tr><td colspan="12" class="loading-holdings" style="color: var(--accent-red);">구글 스프레드시트 보유 종목 데이터를 불러오지 못했습니다. 연동 설정을 확인하십시오.</td></tr>`;
        }
    }

    async function renderGspreadPortfolio(holdings) {
        if (!holdingsList) return;
        
        if (!holdings || holdings.length === 0) {
            holdingsList.innerHTML = `<tr><td colspan="12" class="loading-holdings">보유 중인 종목이 없습니다. (보유량 > 0 필터링)</td></tr>`;
            return;
        }

        // Calculate aggregates
        let totalInvested = 0.0;
        let totalEvaluation = 0.0;

        holdings.forEach(item => {
            const isKRW = item.ticker.toLowerCase().includes(".ks") || item.ticker.toUpperCase() === "CASH";
            const rate = isKRW ? 1.0 : exchangeRateUSD;
            
            totalInvested += (item.total_purchase || 0.0) * rate;
            totalEvaluation += (item.total_evaluation || 0.0) * rate;
        });

        const totalProfit = totalEvaluation - totalInvested;
        const totalROI = totalInvested > 0 ? (totalProfit / totalInvested) * 100 : 0.0;

        // Render summary bar
        const summaryBar = document.getElementById("portfolio-summary-bar");
        if (summaryBar) {
            const profitClass = totalProfit > 0 ? "pos-return" : (totalProfit < 0 ? "neg-return" : "");
            const profitSign = totalProfit > 0 ? "+" : "";
            const roiSign = totalROI > 0 ? "+" : "";
            
            summaryBar.innerHTML = `
                <div class="summary-card">
                    <span class="summary-label">총 투자금액</span>
                    <span class="summary-value">${Math.round(totalInvested).toLocaleString('ko-KR')}원</span>
                </div>
                <div class="summary-card profit-card ${profitClass}">
                    <span class="summary-label">총 평가손익</span>
                    <span class="summary-value">${profitSign}${Math.round(totalProfit).toLocaleString('ko-KR')}원</span>
                </div>
                <div class="summary-card profit-card ${profitClass}">
                    <span class="summary-label">총 수익률</span>
                    <span class="summary-value">${roiSign}${totalROI.toFixed(2)}%</span>
                </div>
            `;
        }

        holdingsList.innerHTML = "";
        
        function formatCurrency(val, isKRW) {
            if (isKRW) {
                return Math.round(val).toLocaleString('ko-KR') + "원";
            } else {
                return "$" + val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
        }

        holdings.forEach((item, index) => {
            const tr = document.createElement("tr");
            
            const isKRW = item.ticker.toLowerCase().includes(".ks") || item.ticker.toUpperCase() === "CASH";
            const rate = isKRW ? 1.0 : exchangeRateUSD;
            const profitVal = parseFloat(item.profit) || 0.0;
            const isPositive = profitVal > 0;
            const isNegative = profitVal < 0;
            
            let returnClass = "";
            if (isPositive) returnClass = "pos-return";
            else if (isNegative) returnClass = "neg-return";
            
            const stockEvalKRW = (item.total_evaluation || 0.0) * rate;
            const evalWeightPct = totalEvaluation > 0 ? (stockEvalKRW / totalEvaluation) * 100 : 0.0;
            const formattedEvalWeight = evalWeightPct.toFixed(2) + "%";
            
            const formattedQty = item.quantity.toLocaleString('en-US', { maximumFractionDigits: 4 });
            const formattedPrice = formatCurrency(item.current_price, isKRW);
            const formattedPurchase = formatCurrency(item.purchase_price, isKRW);
            const formattedTotalPurchase = formatCurrency(item.total_purchase, isKRW);
            const formattedTotalEval = formatCurrency(item.total_evaluation, isKRW);
            
            let formattedProfit = formatCurrency(Math.abs(profitVal), isKRW);
            if (isPositive) formattedProfit = "+" + formattedProfit;
            else if (isNegative) formattedProfit = "-" + formattedProfit;
            
            const accountType = item.account_type || "일반주식";
            const badgeClass = accountType === "개인연금" ? "badge-pension" : "badge-stock";
            const badgeHtml = `<span class="badge ${badgeClass}">${accountType}</span>`;
            
            tr.innerHTML = `
                <td>${badgeHtml}</td>
                <td class="ticker-cell">${item.ticker.toUpperCase()}</td>
                <td class="mobile-ellipsis">${item.name}</td>
                <td class="number-cell hide-on-mobile">${formattedQty}</td>
                <td class="number-cell">${formattedPrice}</td>
                <td class="number-cell hide-on-mobile">${formattedPurchase}</td>
                <td class="number-cell hide-on-mobile">${formattedTotalPurchase}</td>
                <td class="number-cell hide-on-mobile">${formattedTotalEval}</td>
                <td class="number-cell ${returnClass}">${formattedProfit}</td>
                <td class="number-cell ${returnClass}">${item.roi}</td>
                <td class="number-cell hide-on-mobile" style="font-family: 'Orbitron', monospace;">${item.weight}</td>
                <td class="number-cell" style="font-family: 'Orbitron', monospace; color: var(--accent-cyan);">${formattedEvalWeight}</td>
                <td style="text-align: center;">
                    <div class="trend-container">
                        <div class="sparkline-container" data-ticker="${item.ticker}" data-index="${index}" title="상세 차트 보기" style="cursor: pointer;">
                            <span class="skeleton-placeholder" style="width: 120px; height: 34px; display: inline-block; margin-top: 2px;"></span>
                        </div>
                    </div>
                </td>
            `;
            
            holdingsList.appendChild(tr);
        });
        
        // Ensure sort header UI is kept in sync when rendered (e.g. after refresh)
        updateSortHeadersUI();
        loadSparklinesForHoldings();
    }

    function sortHoldings(key) {
        if (!portfolioHoldings || portfolioHoldings.length === 0) return;
        
        if (currentSortKey === key) {
            currentSortOrder = currentSortOrder === "asc" ? "desc" : "asc";
        } else {
            currentSortKey = key;
            // Default to descending for numbers, ascending for strings
            const numericKeys = ["quantity", "current_price", "purchase_price", "total_purchase", "total_evaluation", "profit", "roi", "weight", "eval_weight", "trend_pct"];
            currentSortOrder = numericKeys.includes(key) ? "desc" : "asc";
        }

        portfolioHoldings.sort((a, b) => {
            // Force account_type grouping when sorting by other columns
            if (key !== "account_type") {
                const typeA = a.account_type || "일반주식";
                const typeB = b.account_type || "일반주식";
                if (typeA !== typeB) {
                    return typeA === "개인연금" ? -1 : 1;
                }
            }

            let valA, valB;

            if (key === "eval_weight") {
                const rateA = (a.ticker.toLowerCase().includes(".ks") || a.ticker.toUpperCase() === "CASH") ? 1.0 : exchangeRateUSD;
                const rateB = (b.ticker.toLowerCase().includes(".ks") || b.ticker.toUpperCase() === "CASH") ? 1.0 : exchangeRateUSD;
                valA = (a.total_evaluation || 0.0) * rateA;
                valB = (b.total_evaluation || 0.0) * rateB;
            } else if (key === "roi") {
                valA = parseFloat(a.roi.replace("%", "")) || 0.0;
                valB = parseFloat(b.roi.replace("%", "")) || 0.0;
            } else if (key === "weight") {
                valA = parseFloat(a.weight.replace("%", "")) || 0.0;
                valB = parseFloat(b.weight.replace("%", "")) || 0.0;
            } else if (key === "trend_pct") {
                valA = a.trend_pct !== undefined && a.trend_pct !== null ? a.trend_pct : -999999;
                valB = b.trend_pct !== undefined && b.trend_pct !== null ? b.trend_pct : -999999;
            } else if (key === "quantity" || key === "current_price" || key === "purchase_price" || key === "total_purchase" || key === "total_evaluation" || key === "profit") {
                valA = parseFloat(a[key]) || 0.0;
                valB = parseFloat(b[key]) || 0.0;
            } else {
                valA = a[key] ? a[key].toString().toLowerCase() : "";
                valB = b[key] ? b[key].toString().toLowerCase() : "";
            }

            if (valA < valB) return currentSortOrder === "asc" ? -1 : 1;
            if (valA > valB) return currentSortOrder === "asc" ? 1 : -1;
            return 0;
        });

        renderGspreadPortfolio(portfolioHoldings);
    }

    function updateSortHeadersUI() {
        const headers = document.querySelectorAll("#holdings-table th.sortable");
        headers.forEach(th => {
            const key = th.getAttribute("data-sort");
            const iconSpan = th.querySelector(".sort-icon");
            if (iconSpan) {
                if (key === currentSortKey) {
                    iconSpan.innerText = currentSortOrder === "asc" ? "▲" : "▼";
                    th.classList.add("active-sort");
                } else {
                    iconSpan.innerText = "↕";
                    th.classList.remove("active-sort");
                }
            }
        });
    }

    function tryRenderCharts() {
        if (portfolioHoldings && portfolioSettings) {
            // Use dynamic target allocation if available, fallback to static target_allocation
            const targetAlloc = portfolioSettings.dynamic_target_allocation || portfolioSettings.target_allocation || { cash: 0.1, stock: 0.5, bond: 0.2, gold: 0.1, commodity: 0.1 };
            const cashVal = portfolioSettings.cash || 0;
            updateAllocationCharts(portfolioHoldings, targetAlloc, cashVal, exchangeRateUSD);
            
            // Display dynamic rules triggers in UI
            renderDynamicRulesUI(portfolioSettings.rules_status);
        }
    }

    function renderDynamicRulesUI(rulesStatus) {
        const rulesBar = document.getElementById("dynamic-rules-bar");
        const rulesTriggers = document.getElementById("dynamic-rules-triggers");
        if (!rulesBar || !rulesTriggers) return;
        
        if (!rulesStatus) {
            rulesBar.classList.add("hidden");
            rulesBar.style.display = "none";
            return;
        }
        
        rulesBar.classList.remove("hidden");
        rulesBar.style.display = "flex";
        
        let html = "";
        
        // Rule 1: Yield
        const yVal = rulesStatus.yield_30y !== null && rulesStatus.yield_30y !== undefined ? rulesStatus.yield_30y.toFixed(2) + "%" : "로딩 실패";
        if (rulesStatus.yield_30y_triggered) {
            html += `<span style="background: rgba(0, 242, 254, 0.1); border: 1px solid var(--accent-cyan); color: #00f2fe; padding: 4px 8px; border-radius: 4px; display: flex; align-items: center; gap: 5px;">
                🔴 <strong>Rule 1 활성화 (US 30Y Yield: ${yVal})</strong>: 채권 비중 +5% 상향 (현금에서 차감)
            </span>`;
        } else {
            html += `<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 4px 8px; border-radius: 4px;">
                ⚪ Rule 1 비활성 (US 30Y Yield: ${yVal})
            </span>`;
        }
        
        // Rule 2: VIX
        const vVal = rulesStatus.vix !== null && rulesStatus.vix !== undefined ? rulesStatus.vix.toFixed(2) : "로딩 실패";
        if (rulesStatus.vix_triggered) {
            html += `<span style="background: rgba(255, 77, 77, 0.1); border: 1px solid #ff4d4d; color: #ff4d4d; padding: 4px 8px; border-radius: 4px; display: flex; align-items: center; gap: 5px;">
                🛡️ <strong>Rule 2 보호모드 (VIX: ${vVal})</strong>: 테크 비중 축소 (주식 -10%, 현금 +10%)
            </span>`;
        } else {
            html += `<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 4px 8px; border-radius: 4px;">
                ⚪ Rule 2 비활성 (VIX: ${vVal})
            </span>`;
        }
        
        rulesTriggers.innerHTML = html;
    }

    function updateAllocationCharts(holdings, targetAllocation, cashBase, exchangeRate) {
        let totalEvaluation = 0;
        // cashBase는 holdings에 포함된 asset_class="cash" 항목의 총합이므로 별도로 더하지 않음
        let classValues = { stock: 0, bond: 0, gold: 0, commodity: 0, cash: 0 };

        holdings.forEach(item => {
            // CASH 티커는 KRW 자산 / .ks로 끝나는 한국 주식도 KRW
            const isKRW = item.ticker.toLowerCase().includes(".ks") || item.ticker.toUpperCase() === "CASH";
            const rate = isKRW ? 1.0 : exchangeRate;
            const evalKRW = (item.total_evaluation || 0.0) * rate;
            
            totalEvaluation += evalKRW;
            const assetClass = item.asset_class || "stock";
            if (classValues[assetClass] !== undefined) {
                classValues[assetClass] += evalKRW;
            } else {
                classValues[assetClass] = evalKRW;
            }
        });

        // holdings에 cash 자산이 없을 경우, cashBase를 별도 현금으로 추가
        if (classValues.cash === 0 && cashBase > 0) {
            classValues.cash = cashBase;
            totalEvaluation += cashBase;
        }
        
        const totalPortfolioValue = totalEvaluation;
        
        const currentWeights = {
            cash: totalPortfolioValue > 0 ? (classValues.cash / totalPortfolioValue) : 0,
            stock: totalPortfolioValue > 0 ? (classValues.stock / totalPortfolioValue) : 0,
            bond: totalPortfolioValue > 0 ? (classValues.bond / totalPortfolioValue) : 0,
            gold: totalPortfolioValue > 0 ? (classValues.gold / totalPortfolioValue) : 0,
            commodity: totalPortfolioValue > 0 ? (classValues.commodity / totalPortfolioValue) : 0
        };

        const targetWeights = {
            cash: targetAllocation.cash || 0.1,
            stock: targetAllocation.stock || 0.5,
            bond: targetAllocation.bond || 0.2,
            gold: targetAllocation.gold || 0.1,
            commodity: targetAllocation.commodity || 0.1
        };

        // Render Pie Chart
        const pieCanvas = document.getElementById('allocation-pie-chart');
        if (pieCanvas) {
            const pieCtx = pieCanvas.getContext('2d');
            if (pieChart) pieChart.destroy();
            
            pieChart = new Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: ['현금 (Cash)', '주식 (Stock)', '채권 (Bond)', '금 (Gold)', '원자재 (Commodity)'],
                    datasets: [{
                        data: [
                            (currentWeights.cash * 100).toFixed(1),
                            (currentWeights.stock * 100).toFixed(1),
                            (currentWeights.bond * 100).toFixed(1),
                            (currentWeights.gold * 100).toFixed(1),
                            (currentWeights.commodity * 100).toFixed(1)
                        ],
                        backgroundColor: [
                            '#475569',   // Cash: Slate Grey
                            '#0ea5e9',   // Stock: Sky Blue
                            '#8b5cf6',   // Bond: Violet Purple
                            '#eab308',   // Gold: Golden Yellow
                            '#f97316'    // Commodity: Amber Orange
                        ],
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#f1f3f9', font: { family: 'Inter', size: 10 } }
                        },
                        title: {
                            display: true,
                            text: '현재 자산 배분 비중 (%)',
                            color: '#f1f3f9',
                            font: { family: 'Inter', weight: 'bold' }
                        }
                    }
                }
            });
        }

        // Render Compare Bar Chart
        const compareCanvas = document.getElementById('allocation-compare-chart');
        if (compareCanvas) {
            const compareCtx = compareCanvas.getContext('2d');
            if (compareChart) compareChart.destroy();

            // Create gradients for compare bars
            const gCompareCurr = compareCtx.createLinearGradient(0, 0, 0, 300);
            gCompareCurr.addColorStop(0, 'rgba(0, 242, 254, 0.85)');
            gCompareCurr.addColorStop(1, 'rgba(79, 172, 254, 0.35)');

            const gCompareTarget = compareCtx.createLinearGradient(0, 0, 0, 300);
            gCompareTarget.addColorStop(0, 'rgba(154, 162, 177, 0.45)');
            gCompareTarget.addColorStop(1, 'rgba(154, 162, 177, 0.15)');

            compareChart = new Chart(compareCtx, {
                type: 'bar',
                data: {
                    labels: ['현금', '주식', '채권', '금', '원자재'],
                    datasets: [
                        {
                            label: '현재 비중 (%)',
                            data: [
                                (currentWeights.cash * 100).toFixed(1),
                                (currentWeights.stock * 100).toFixed(1),
                                (currentWeights.bond * 100).toFixed(1),
                                (currentWeights.gold * 100).toFixed(1),
                                (currentWeights.commodity * 100).toFixed(1)
                            ],
                            backgroundColor: gCompareCurr,
                            borderColor: 'rgba(0, 210, 255, 0.8)',
                            borderWidth: 1
                        },
                        {
                            label: '목표 비중 (%)',
                            data: [
                                (targetWeights.cash * 100).toFixed(1),
                                (targetWeights.stock * 100).toFixed(1),
                                (targetWeights.bond * 100).toFixed(1),
                                (targetWeights.gold * 100).toFixed(1),
                                (targetWeights.commodity * 100).toFixed(1)
                            ],
                            backgroundColor: gCompareTarget,
                            borderColor: 'rgba(154, 162, 177, 0.6)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: '#9aa2b1' }, grid: { display: false } },
                        y: { ticks: { color: '#9aa2b1' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#f1f3f9', font: { family: 'Inter', size: 10 } }
                        },
                        title: {
                            display: true,
                            text: '현재 vs 목표 비중 비교',
                            color: '#f1f3f9',
                            font: { family: 'Inter', weight: 'bold' }
                        }
                    }
                }
            });
        }
    }

    // ==========================================================================
    // Rebalance Strategy & Action Card Parser
    // ==========================================================================

    async function loadRebalanceStrategy() {
        if (!rebalanceStrategyDisplay) return;
        try {
            const response = await fetch(`${API_PORTFOLIO_REBALANCE}?_t=${Date.now()}`);
            if (response.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (response.ok) {
                const data = await response.json();
                if (data && data.content) {
                    rebalanceStrategyDisplay.innerHTML = parseMarkdown(data.content);
                    parseRebalanceCards(data.content);
                }
            }
        } catch (error) {
            console.warn("Failed to load cached rebalance strategy:", error);
        }
    }

    async function generateRebalanceStrategy() {
        const apiKey = localStorage.getItem("gemini_api_key") || "";
        if (!apiKey) {
            btnOpenSettings.click();
            setTimeout(() => {
                inputGeminiApiKey.focus();
            }, 300);
            return;
        }
        
        const selectedModel = selectGeminiModel ? selectGeminiModel.value : "gemini-2.5-flash";
        const btnTextEl = btnGenerateRebalance.querySelector(".btn-text");
        const btnLoaderEl = btnGenerateRebalance.querySelector(".btn-loader");
        
        btnGenerateRebalance.disabled = true;
        if (btnLoaderEl) btnLoaderEl.classList.remove("hidden");
        if (btnTextEl) btnTextEl.innerText = "리밸런싱 전략 생성 중...";
        
        if (rebalanceCardsContainer) {
            rebalanceCardsContainer.innerHTML = `
                <div class="skeleton-card"></div>
                <div class="skeleton-card"></div>
                <div class="skeleton-card"></div>
            `;
        }
        
        try {
            const response = await fetch(API_PORTFOLIO_REBALANCE, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: apiKey, model: selectedModel })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || errorData.error || "API call failed");
            }
            
            const data = await response.json();
            rebalanceStrategyDisplay.innerHTML = parseMarkdown(data.content);
            parseRebalanceCards(data.content);
            addTerminalLine("[SUCCESS] AI 포트폴리오 리밸런싱 전략이 성공적으로 생성되었습니다.", "success-line");
            if (data.gdoc_link) {
                addTerminalLine(`[SUCCESS] 리밸런싱 구글 드라이브 업로드 주소: ${data.gdoc_link}`, "success-line");
            }
            loadReportsList();
        } catch (error) {
            console.error("Failed to generate rebalance strategy:", error);
            if (rebalanceCardsContainer) {
                rebalanceCardsContainer.innerHTML = `<div class="loading-holdings" style="color: var(--accent-red); grid-column: 1 / -1; text-align: center; padding: 30px 0;">
                    리밸런싱 전략을 생성하지 못했습니다: ${error.message}
                </div>`;
            }
            addTerminalLine(`[SYSTEM ERROR] 리밸런싱 전략 생성 실패: ${error.message}`, "error-line");
        } finally {
            btnGenerateRebalance.disabled = false;
            if (btnLoaderEl) btnLoaderEl.classList.add("hidden");
            if (btnTextEl) btnTextEl.innerText = "AI 리밸런싱 전략 생성 및 업데이트";
        }
    }

    function parseRebalanceCards(content) {
        if (!rebalanceCardsContainer) return;

        const lines = content.split("\n");
        let tableRows = [];

        for (let line of lines) {
            line = line.trim();
            if (line.startsWith("|") && line.endsWith("|")) {
                if (line.includes("---") || line.includes("종목명") || line.includes("현재 비중")) {
                    continue; // Skip headers/separators
                }
                const cells = line.split("|").map(c => c.trim()).filter(c => c !== "");
                if (cells.length >= 6) {
                    tableRows.push(cells);
                }
            }
        }

        if (tableRows.length === 0) {
            rebalanceCardsContainer.innerHTML = `<div class="loading-holdings" style="grid-column: 1 / -1; text-align: center; padding: 20px 0; font-size: 13px; color: var(--text-secondary);">
                전략 세부 텍스트 보고서 보관소를 참조하십시오. (규격 테이블 파싱 실패)
            </div>`;
            rebalanceStrategyDisplay.classList.remove("hidden");
            return;
        }

        rebalanceCardsContainer.innerHTML = "";
        rebalanceStrategyDisplay.classList.add("hidden"); // Hide markdown default

        // Map and categorize action types for sorting
        let parsedCards = [];
        tableRows.forEach(row => {
            // Columns: | 종목명 (티커) | 현재 비중 | 제안 액션 | 제안 비중/방향 | 진입 점수 | 평가 점수 | 핵심 근거 |
            const nameTicker = row[0];
            const currentWeight = row[1];
            const action = row[2];
            const proposedWeight = row[3];
            const entryScore = row[4];
            const evalScore = row[5];
            const rationale = row[6] || "";

            let actionType = "HOLD";
            if (action.includes("매수") || action.includes("신규") || action.toUpperCase().includes("BUY")) {
                actionType = "BUY";
            } else if (action.includes("매도") || action.includes("축소") || action.toUpperCase().includes("SELL")) {
                actionType = "SELL";
            }

            parsedCards.push({ nameTicker, currentWeight, action, proposedWeight, entryScore, evalScore, rationale, actionType });
        });

        // Sort: BUY -> SELL -> HOLD
        const actionPriority = { "BUY": 1, "SELL": 2, "HOLD": 3 };
        parsedCards.sort((a, b) => actionPriority[a.actionType] - actionPriority[b.actionType]);

        parsedCards.forEach(cardData => {
            const { nameTicker, currentWeight, action, proposedWeight, entryScore, evalScore, rationale, actionType } = cardData;
            
            let ticker = nameTicker;
            let name = nameTicker;
            const tickerMatch = nameTicker.match(/\(([^)]+)\)/);
            if (tickerMatch) {
                ticker = tickerMatch[1];
                name = nameTicker.replace(/\([^)]+\)/, "").trim();
            }

            let actionClass = "action-hold";
            let actionLabel = action;
            if (actionType === "BUY") {
                actionClass = "action-buy";
                actionLabel = "BUY / 매수";
            } else if (actionType === "SELL") {
                actionClass = "action-sell";
                actionLabel = "SELL / 매도";
            } else {
                actionClass = "action-hold";
                actionLabel = "HOLD / 유지";
            }

            const card = document.createElement("div");
            card.className = `rebalance-action-card ${actionClass}`;

            card.innerHTML = `
                <span class="action-badge">${actionLabel}</span>
                <div class="rebalance-card-ticker">${ticker.toUpperCase()}</div>
                <div class="rebalance-card-name">${name}</div>
                <div class="rebalance-card-qty" style="color: var(--accent-cyan);">추천 비중: ${proposedWeight}</div>
                <div class="rebalance-card-weight">
                    <span>현재 비중: <strong>${currentWeight}</strong></span>
                </div>
                <div style="display: flex; gap: 10px; font-size: 11px; margin-top: 8px; color: var(--text-secondary);">
                    <span>진입: <strong>${entryScore}</strong></span>
                    <span>평가: <strong>${evalScore}</strong></span>
                </div>
                <div class="rebalance-card-reason">${rationale}</div>
            `;

            rebalanceCardsContainer.appendChild(card);
        });
    }

    // ==========================================================================
    // Report Archiver Functions
    // ==========================================================================

    async function loadReportsList() {
        let serverReports = [];
        try {
            const response = await fetch(`${API_REPORTS}?_t=${Date.now()}`);
            if (response.status === 401) {
                window.location.href = "/login.html";
                return;
            }
            if (response.ok) {
                serverReports = await response.json();
            }
        } catch (error) {
            console.warn("Could not load reports from server:", error);
        }
        
        let localReports = [];
        try {
            localReports = JSON.parse(localStorage.getItem("reports_archive")) || [];
        } catch (e) {
            localReports = [];
        }
        
        const allReportsMap = new Map();
        serverReports.forEach(filename => {
            allReportsMap.set(filename, { filename, isLocalOnly: false });
        });
        localReports.forEach(item => {
            allReportsMap.set(item.filename, { filename: item.filename, isLocalOnly: true, content: item.content });
        });
        
        const sortedReports = Array.from(allReportsMap.values()).sort((a, b) => b.filename.localeCompare(a.filename));
        renderReportsList(sortedReports);
    }

    function getReportDisplayName(filename) {
        const rebalanceMatch = filename.match(/^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})_rebalance/i);
        if (rebalanceMatch) {
            return `⚖️ 리밸런싱 전략 (${rebalanceMatch[1]} ${rebalanceMatch[2]}:${rebalanceMatch[3]}:${rebalanceMatch[4]})`;
        }
        const reportMatch = filename.match(/^(\d{4}-\d{2}-\d{2})_report/i);
        if (reportMatch) {
            return `📈 추천 보고서 (${reportMatch[1]})`;
        }
        if (filename.toLowerCase().includes("rebalance") || filename.toLowerCase().includes("strategy")) {
            return `⚖️ 리밸런싱 전략 (${filename.replace(".md", "")})`;
        }
        return `📈 보고서 (${filename.replace(".md", "")})`;
    }

    function renderReportsList(reports) {
        reportsList.innerHTML = "";
        
        if (reports.length === 0) {
            reportsList.innerHTML = '<li class="empty-item">보관된 보고서가 없습니다.</li>';
            return;
        }

        reports.forEach(item => {
            const li = document.createElement("li");
            
            const nameSpan = document.createElement("span");
            nameSpan.className = "report-file-name";
            nameSpan.innerText = getReportDisplayName(item.filename);
            
            const btnView = document.createElement("button");
            btnView.className = "btn-report-view";
            btnView.innerText = "보기";
            btnView.addEventListener("click", (e) => {
                e.stopPropagation();
                viewReport(item);
            });

            li.appendChild(nameSpan);
            li.appendChild(btnView);
            li.addEventListener("click", () => viewReport(item));
            
            reportsList.appendChild(li);
        });
    }

    async function viewReport(item) {
        if (item.isLocalOnly && item.content) {
            renderReportInViewer(item.filename, item.content);
        } else {
            try {
                const response = await fetch(`${API_REPORTS}/${item.filename}?_t=${Date.now()}`);
                if (!response.ok) throw new Error("Failed to retrieve report content");
                
                const data = await response.json();
                renderReportInViewer(data.filename, data.content);
            } catch (error) {
                console.error("Failed to view report:", error);
                alert(`보고서를 로드하지 못했습니다: ${error.message}`);
            }
        }
    }

    function renderReportInViewer(filename, content) {
        viewingReportTitle.innerText = `${filename.replace(".md", "")} 투자 종목 추천 리포트`;
        reportMdDisplay.innerHTML = parseMarkdown(content);
        reportViewerSection.classList.remove("hidden");
        reportViewerSection.scrollIntoView({ behavior: "smooth" });
    }

    // A lightweight, offline-ready Regex Markdown Parser
    function parseMarkdown(md) {
        let html = md;
        
        html = html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
        
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
        html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
        
        html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');
        
        let lines = html.split('\n');
        let inTable = false;
        let tableHtml = "";
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            if (line.startsWith('|') && line.endsWith('|')) {
                if (!inTable) {
                    inTable = true;
                    tableHtml = "<table>";
                }
                
                if (line.includes('---')) {
                    lines[i] = "";
                    continue;
                }
                
                let cells = line.split('|').slice(1, -1);
                let tag = (tableHtml === "<table>") ? "th" : "td";
                tableHtml += "<tr>" + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + "</tr>";
                lines[i] = "";
            } else {
                if (inTable) {
                    inTable = false;
                    tableHtml += "</table>";
                    lines[i-1] += "\n" + tableHtml;
                    tableHtml = "";
                }
            }
        }
        
        html = lines.filter(l => l !== "").join('\n');
        
        html = html.replace(/\n\n/g, '<p></p>');
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }

    // Sparkline & Detailed Modal functions
    function generateSparklineSVG(prices, volumes) {
        if (!prices || prices.length < 2) return "";
        
        const width = 120;
        const height = 34;
        const padding = 2;

        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const priceRange = maxPrice - minPrice || 1;

        const points = prices.map((price, idx) => {
            const x = padding + (idx / (prices.length - 1)) * (width - padding * 2);
            const y = height - padding - ((price - minPrice) / priceRange) * (height - padding * 2);
            return `${x},${y}`;
        });
        
        const pathData = `M ${points.join(" L ")}`;

        const maxVol = Math.max(...volumes) || 1;
        const barWidth = Math.floor((width - padding * 2) / volumes.length) - 1;
        
        let barsHTML = "";
        volumes.forEach((vol, idx) => {
            const x = padding + idx * (barWidth + 1);
            const barHeight = (vol / maxVol) * (height * 0.45);
            const y = height - barHeight;
            
            barsHTML += `<rect x="${x}" y="${y}" width="${Math.max(1, barWidth)}" height="${barHeight}" fill="var(--accent-purple)" opacity="0.35" rx="0.5" />`;
        });

        return `
            <svg width="${width}" height="${height}" class="sparkline-svg">
                ${barsHTML}
                <path d="${pathData}" stroke="var(--accent-cyan)" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0px 0px 3px rgba(0, 242, 254, 0.6));" />
            </svg>
        `;
    }

    async function loadSparklinesForHoldings() {
        const containers = document.querySelectorAll("#holdings-list .sparkline-container");
        containers.forEach(async (container) => {
            const index = container.dataset.index;
            if (index === undefined) return;
            
            const item = portfolioHoldings ? portfolioHoldings[index] : null;
            if (!item) return;

            const ticker = item.ticker;
            if (!ticker) return;

            if (ticker.toUpperCase() === "CASH") {
                container.innerHTML = `<span style="color: var(--text-muted); font-size: 0.8rem;">-</span>`;
                item.trend_pct = null;
                return;
            }

            // Already fetched? Use it
            if (item.sparkline_prices) {
                renderSparklineDOM(container, item.sparkline_prices, item.sparkline_volumes, item.trend_pct);
                return;
            }

            try {
                const resp = await fetch(`/api/screener/history/${ticker}?period=1mo`);
                if (!resp.ok) throw new Error(`Failed to fetch history for ${ticker}`);
                const data = await resp.json();
                
                item.sparkline_prices = data.prices;
                item.sparkline_volumes = data.volumes;
                
                let trendPct = null;
                const validPrices = (data.prices || []).filter(p => p !== null && p !== undefined);
                if (validPrices.length >= 2) {
                    const first = validPrices[0];
                    const last = validPrices[validPrices.length - 1];
                    trendPct = (last - first) / first * 100;
                }
                item.trend_pct = trendPct;

                renderSparklineDOM(container, item.sparkline_prices, item.sparkline_volumes, item.trend_pct);
            } catch (err) {
                console.error(`Failed to load sparkline for ${ticker}:`, err);
                container.innerHTML = `<span style="color: var(--accent-red); font-size: 0.8rem;">Error</span>`;
            }
        });
    }

    function renderSparklineDOM(container, prices, volumes, trendPct) {
        const svg = generateSparklineSVG(prices, volumes);
        let trendPctBadge = '';
        if (trendPct !== null && trendPct !== undefined) {
            const sign = trendPct >= 0 ? '+' : '';
            const cls = trendPct > 0.5 ? 'trend-pct-up' : trendPct < -0.5 ? 'trend-pct-down' : 'trend-pct-flat';
            const arrow = trendPct > 0.5 ? '▲' : trendPct < -0.5 ? '▼' : '—';
            trendPctBadge = `<div class="trend-pct-badge ${cls}">${arrow} ${sign}${trendPct.toFixed(2)}%</div>`;
        }

        if (svg) {
            container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; gap:2px;">
                ${svg}
                ${trendPctBadge}
            </div>`;
        } else {
            container.innerHTML = `<span style="color: var(--text-muted); font-size: 0.8rem;">-</span>`;
        }
    }

    let detailChartInstance = null;
    const modalChart = document.getElementById('chart-modal');
    const modalChartTitle = document.getElementById('modal-title');
    const modalChartLoading = document.getElementById('modal-loading');
    const chartCanvas = document.getElementById('detailChart');
    const btnCloseChart = document.getElementById('btn-close-chart');

    function closeChartModal() {
        if (modalChart) modalChart.classList.remove('active');
    }

    if (btnCloseChart) {
        btnCloseChart.addEventListener('click', closeChartModal);
    }
    if (modalChart) {
        modalChart.addEventListener('click', (e) => {
            if (e.target === modalChart) closeChartModal();
        });
    }

    async function openChartModal(ticker) {
        if (!modalChart) return;
        modalChart.classList.add('active');
        if (modalChartTitle) modalChartTitle.innerText = `${ticker.toUpperCase()} - 1Year Trend (MA5, MA20, MA200)`;
        if (modalChartLoading) modalChartLoading.style.display = 'block';
        if (chartCanvas) chartCanvas.style.display = 'none';

        try {
            const resp = await fetch(`/api/screener/history/${ticker}?period=1y`);
            if (!resp.ok) throw new Error('Failed to fetch 1y history');
            const data = await resp.json();
            
            if (modalChartLoading) modalChartLoading.style.display = 'none';
            if (chartCanvas) chartCanvas.style.display = 'block';
            
            renderChartJs(data);
        } catch (err) {
            console.error(err);
            if (modalChartLoading) {
                modalChartLoading.innerHTML = `<span style="color: var(--accent-red);">데이터 로딩 중 오류가 발생했습니다.</span>`;
            }
        }
    }

    function renderChartJs(data) {
        if (!chartCanvas) return;
        if (detailChartInstance) {
            detailChartInstance.destroy();
        }
        
        const ctx = chartCanvas.getContext('2d');
        
        detailChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: '주가 (Close)',
                        data: data.prices,
                        borderColor: '#00d2ff',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: '5일선 (MA5)',
                        data: data.ma5,
                        borderColor: '#00ff66',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: '20일선 (MA20)',
                        data: data.ma20,
                        borderColor: '#ff00ff',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: '200일선 (MA200)',
                        data: data.ma200,
                        borderColor: '#ff9900',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: '거래량 (Volume)',
                        data: data.volumes,
                        backgroundColor: 'rgba(139, 92, 246, 0.3)',
                        borderColor: 'rgba(139, 92, 246, 0.7)',
                        borderWidth: 1,
                        type: 'bar',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#cbd5e1',
                            font: { family: 'Inter' }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            maxTicksLimit: 12,
                            font: { family: 'Roboto Mono', size: 10 }
                        }
                    },
                    y: {
                        position: 'left',
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Roboto Mono', size: 10 }
                        }
                    },
                    y1: {
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        min: 0,
                        suggestedMax: data.volumes && data.volumes.length ? Math.max(...data.volumes) * 3 : undefined,
                        ticks: {
                            color: '#a78bfa',
                            font: { family: 'Roboto Mono', size: 10 },
                            callback: function(value) {
                                if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
                                if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
                                return value;
                            }
                        }
                    }
                }
            }
        });
    }

    if (holdingsList) {
        holdingsList.addEventListener("click", (e) => {
            const sparkline = e.target.closest('.sparkline-container');
            if (sparkline) {
                const ticker = sparkline.dataset.ticker;
                if (ticker && ticker.toUpperCase() !== "CASH") {
                    openChartModal(ticker);
                }
            }
        });
    }

    window.closeChartModal = closeChartModal;
});
