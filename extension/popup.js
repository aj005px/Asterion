const API_URL = "http://127.0.0.1:8000";

async function checkBackendConnection() {
    const indicator = document.getElementById("statusIndicator");
    const statusText = document.getElementById("connectionStatus");
    
    try {
        const response = await fetch(`${API_URL}/recommendations`, { 
            method: "GET",
            cache: "no-cache"
        });
        if (response.ok) {
            indicator.className = "status-dot connected";
            statusText.textContent = "Backend online";
            statusText.style.color = "#000000";
        } else {
            indicator.className = "status-dot error";
            statusText.textContent = "Backend error";
            statusText.style.color = "#000000";
        }
    } catch (error) {
        indicator.className = "status-dot error";
        statusText.textContent = "Backend offline";
        statusText.style.color = "#000000";
        console.error("Asterion connection error:", error);
    }
}

async function showCurrentTab() {
    const urlElement = document.getElementById("url");
    const domainElement = document.getElementById("domain");

    try {
        const [tab] = await chrome.tabs.query({
            active: true,
            currentWindow: true
        });

        if (!tab || !tab.url) {
            urlElement.textContent = "No accessible tab";
            domainElement.textContent = "-";
            return;
        }

        if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://") || 
            tab.url.startsWith("edge://") || tab.url.startsWith("about:")) {
            urlElement.textContent = "Restricted browser page";
            domainElement.textContent = "-";
            return;
        }

        urlElement.textContent = tab.url;

        try {
            domainElement.textContent = new URL(tab.url).hostname;
        } catch {
            domainElement.textContent = "-";
        }
    } catch (error) {
        urlElement.textContent = "Cannot read tab";
        domainElement.textContent = "-";
        console.error("Asterion popup error:", error);
    }
}

async function sendFeedback(item, label, buttons, status) {
    buttons.forEach(button => {
        button.disabled = true;
    });
    status.textContent = "Saving...";
    status.className = "feedback-status";

    try {
        const response = await fetch(`${API_URL}/feedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                domain: item.domain,
                label: label,
                weighted_score: item.weighted_score,
                time_score: item.time_score,
                activation_score: item.activation_score,
                recency_score: item.recency_score
            })
        });

        if (!response.ok) {
            const errorBody = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorBody}`);
        }

        status.textContent = label === "useful" ? "Saved: useful" : "Saved: not useful";
        status.className = "feedback-status success";
    } catch (error) {
        status.textContent = "Save failed. Try again.";
        status.className = "feedback-status error";
        buttons.forEach(button => {
            button.disabled = false;
        });
        console.error("Asterion feedback error:", error);
    }
}

function createRecommendation(item, index) {
    const card = document.createElement("div");
    card.className = "recommendation-card";

    const header = document.createElement("div");
    header.className = "recommendation-header";

    const rank = document.createElement("span");
    rank.className = "recommendation-rank";
    rank.textContent = `#${index + 1}`;

    const domain = document.createElement("div");
    domain.className = "domain-name";
    domain.textContent = item.domain ? item.domain : "Unknown";

    const score = document.createElement("div");
    score.className = "score-display";
    const weightedScore = Number(item.weighted_score || 0);
    score.textContent = weightedScore.toFixed(3);

    header.append(rank, domain, score);

    const bar = document.createElement("div");
    bar.className = "score-bar";

    const fill = document.createElement("div");
    fill.className = "score-bar-fill";
    fill.style.width = `${Math.max(0, Math.min(1, weightedScore)) * 100}%`;

    bar.appendChild(fill);

    const details = document.createElement("div");
    details.className = "score-details";
    details.textContent = 
        `Time: ${Number(item.time_score||0).toFixed(3)} • Act: ${Number(item.activation_score||0).toFixed(3)} • Rec: ${Number(item.recency_score||0).toFixed(3)}`;

    const feedbackRow = document.createElement("div");
    feedbackRow.className = "feedback-row";

    const usefulButton = document.createElement("button");
    usefulButton.className = "feedback-btn";
    usefulButton.textContent = "Useful";

    const notUsefulButton = document.createElement("button");
    notUsefulButton.className = "feedback-btn";
    notUsefulButton.textContent = "Not useful";

    const status = document.createElement("div");
    status.className = "feedback-status";
    status.setAttribute("aria-live", "polite");

    const buttons = [usefulButton, notUsefulButton];

    usefulButton.addEventListener("click", () => {
        sendFeedback(item, "useful", buttons, status);
    });

    notUsefulButton.addEventListener("click", () => {
        sendFeedback(item, "not_useful", buttons, status);
    });

    feedbackRow.append(usefulButton, notUsefulButton);
    card.append(header, bar, details, feedbackRow, status);

    return card;
}

async function loadRecommendations() {
    const message = document.getElementById("message");
    const container = document.getElementById("recommendations");
    const refreshButton = document.getElementById("refresh");

    message.textContent = "Scanning data...";
    message.className = "message";
    container.replaceChildren();
    refreshButton.disabled = true;

    try {
        const response = await fetch(`${API_URL}/recommendations`);

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.count && data.count > 0) {
            message.textContent = `${data.count} domains`;
        } else {
            message.textContent = "No activity data yet. Start browsing.";
        }

        if (data.recommendations && Array.isArray(data.recommendations)) {
            data.recommendations.forEach((item, index) => {
                container.appendChild(createRecommendation(item, index));
            });
        }
    } catch (error) {
        message.textContent = "Cannot connect to API at 127.0.0.1:8000";
        console.error("Asterion recommendations error:", error);
    } finally {
        refreshButton.disabled = false;
        checkBackendConnection();
    }
}

async function loadTabsToReview() {
    const message = document.getElementById("reviewMessage");
    const container = document.getElementById("tabsToReview");
    const refreshButton = document.getElementById("refreshReview");

    message.textContent = "Scanning open tabs...";
    message.className = "message";
    container.replaceChildren();
    if (refreshButton) {
        refreshButton.disabled = true;
    }

    try {
        // Get all tabs in current window
        const tabs = await chrome.tabs.query({});
        const currentActive = await chrome.tabs.query({ active: true, currentWindow: true });
        const activeId = currentActive && currentActive[0] ? currentActive[0].id : null;

        const candidates = [];
        for (const tab of tabs) {
            // Skip if it's the active tab (exclude by default)
            if (activeId !== null && tab.id === activeId) {
                continue;
            }
            if (tab.pinned) {
                continue;
            }
            // Exclude if playing audio/media when detectable
            if (tab.audible) {
                continue;
            }
            if (tab.discarded) {
                continue;
            }
            const url = tab.url || "";
            // Exclusions for internal pages
            if (url.startsWith("chrome://") || url.startsWith("chrome-extension://") || 
                url.startsWith("edge://") || url.startsWith("about:") ||
                url.startsWith("devtools://") || url.startsWith("chrome-search://") ||
                url.startsWith("chrome-untrusted://") || url.startsWith("moz-extension://")) {
                continue;
            }
            if (!(url.startsWith("http://") || url.startsWith("https://"))) {
                continue;
            }
            candidates.push({
                tab_id: tab.id,
                url: tab.url,
                active: tab.active,
                pinned: tab.pinned,
                audible: tab.audible,
                discarded: tab.discarded,
                window_id: tab.windowId
            });
        }

        const response = await fetch(`${API_URL}/tabs/review`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ tabs: candidates })
        });

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.count && data.count > 0) {
            message.textContent = `${data.count} tab(s) suggested for review`;
        } else {
            message.textContent = "No tabs suggested for review. Not enough activity data or all tabs are excluded.";
        }

        if (data.tabs_to_review && Array.isArray(data.tabs_to_review)) {
            data.tabs_to_review.forEach((item, index) => {
                container.appendChild(createTabReviewCard(item));
            });
        }
    } catch (error) {
        message.textContent = "Cannot load tabs to review. Check API at 127.0.0.1:8000";
        console.error("Asterion tabs review error:", error);
    } finally {
        if (refreshButton) {
            refreshButton.disabled = false;
        }
        checkBackendConnection();
    }
}

function createTabReviewCard(item) {
    const card = document.createElement("div");
    card.className = "recommendation-card";

    const header = document.createElement("div");
    header.className = "recommendation-header";

    const domain = document.createElement("div");
    domain.className = "domain-name";
    domain.textContent = item.domain ? item.domain : "Unknown";

    const score = document.createElement("div");
    score.className = "score-display";
    const reviewScore = Number(item.review_score || 0);
    score.textContent = reviewScore.toFixed(3);

    header.append(domain, score);

    const urlLine = document.createElement("div");
    urlLine.className = "field-value";
    urlLine.style.fontSize = "9px";
    urlLine.style.wordBreak = "break-all";
    urlLine.textContent = item.url || "";

    const reasons = document.createElement("div");
    reasons.className = "score-details";
    if (item.reasons && Array.isArray(item.reasons) && item.reasons.length > 0) {
        reasons.textContent = "Reasons: " + item.reasons.join("; ");
    } else {
        reasons.textContent = "Reasons: Not enough activity data";
    }

    const evidence = document.createElement("div");
    evidence.className = "score-details";
    if (item.evidence && Object.keys(item.evidence).length > 0) {
        const ev = item.evidence;
        const parts = [];
        if (ev.total_time_seconds !== undefined && ev.total_time_seconds !== null) parts.push(`Time: ${Number(ev.total_time_seconds).toFixed(0)}s`);
        if (ev.activation_count !== undefined && ev.activation_count !== null) parts.push(`Acts: ${ev.activation_count}`);
        if (ev.recency_seconds !== undefined && ev.recency_seconds !== null) parts.push(`Rec: ${Math.floor(Number(ev.recency_seconds)/60)}m`);
        evidence.textContent = parts.length > 0 ? parts.join(" • ") : "Evidence: limited";
    } else {
        evidence.textContent = "Evidence: not enough activity data";
    }

    const actions = document.createElement("div");
    actions.className = "feedback-row";

    const closeBtn = document.createElement("button");
    closeBtn.className = "feedback-btn";
    closeBtn.textContent = "Close tab";

    const keepBtn = document.createElement("button");
    keepBtn.className = "feedback-btn";
    keepBtn.textContent = "Keep";

    const status = document.createElement("div");
    status.className = "feedback-status";
    status.setAttribute("aria-live", "polite");

    closeBtn.addEventListener("click", async () => {
        closeBtn.disabled = true;
        keepBtn.disabled = true;
        status.textContent = "Closing...";
        status.className = "feedback-status";
        try {
            if (item.tab_id === undefined || item.tab_id === null) {
                status.textContent = "Cannot close: missing tab ID";
                status.className = "feedback-status error";
                closeBtn.disabled = false;
                keepBtn.disabled = false;
                return;
            }
            await chrome.tabs.remove(item.tab_id);
            status.textContent = "Tab closed";
            status.className = "feedback-status success";
            // Remove card after short delay
            setTimeout(() => {
                card.remove();
            }, 800);
        } catch (error) {
            status.textContent = "Close failed";
            status.className = "feedback-status error";
            closeBtn.disabled = false;
            keepBtn.disabled = false;
            console.error("Asterion close tab error:", error);
        }
    });

    keepBtn.addEventListener("click", () => {
        closeBtn.disabled = true;
        keepBtn.disabled = true;
        status.textContent = "Kept (dismissed)";
        status.className = "feedback-status success";
        setTimeout(() => {
            card.remove();
        }, 600);
    });

    actions.append(closeBtn, keepBtn);
    card.append(header, urlLine, reasons, evidence, actions, status);

    return card;
}

document.getElementById("refresh").addEventListener("click", loadRecommendations);
const refreshReviewBtn = document.getElementById("refreshReview");
if (refreshReviewBtn) {
    refreshReviewBtn.addEventListener("click", loadTabsToReview);
}

checkBackendConnection();
showCurrentTab();
loadRecommendations();
