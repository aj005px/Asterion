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
            indicator.className = "status-indicator connected";
            statusText.textContent = "BACKEND ONLINE";
            statusText.style.color = "#00ff88";
        } else {
            indicator.className = "status-indicator error";
            statusText.textContent = "BACKEND ERROR";
            statusText.style.color = "#ff0040";
        }
    } catch (error) {
        indicator.className = "status-indicator error";
        statusText.textContent = "BACKEND OFFLINE";
        statusText.style.color = "#ff0040";
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
            urlElement.textContent = "NO ACCESSIBLE TAB";
            domainElement.textContent = "UNAVAILABLE";
            return;
        }

        // Don't show sensitive internal pages
        if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://") || 
            tab.url.startsWith("edge://") || tab.url.startsWith("about:")) {
            urlElement.textContent = "RESTRICTED BROWSER PAGE";
            domainElement.textContent = "INTERNAL";
            return;
        }

        urlElement.textContent = tab.url;

        try {
            domainElement.textContent = new URL(tab.url).hostname.toUpperCase();
        } catch {
            domainElement.textContent = "INVALID URL";
        }
    } catch (error) {
        urlElement.textContent = "COULD NOT READ TAB";
        domainElement.textContent = "UNAVAILABLE";
        console.error("Asterion popup error:", error);
    }
}

async function sendFeedback(item, label, buttons, status) {
    buttons.forEach(button => {
        button.disabled = true;
    });
    status.textContent = "SAVING FEEDBACK...";
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

        status.textContent = label === "useful" ? "✓ SAVED: USEFUL" : "✓ SAVED: NOT USEFUL";
        status.className = "feedback-status success";
    } catch (error) {
        status.textContent = "✗ SAVE FAILED - TRY AGAIN";
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
    domain.textContent = item.domain ? item.domain.toUpperCase() : "UNKNOWN";

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
    details.innerHTML = 
        `TIME:${Number(item.time_score||0).toFixed(3)} • ` +
        `ACT:${Number(item.activation_score||0).toFixed(3)} • ` +
        `REC:${Number(item.recency_score||0).toFixed(3)}<br>` +
        `METHOD:${(item.scoring_version||'BASELINE').toUpperCase()} • RANK_SCORE`;

    const feedbackRow = document.createElement("div");
    feedbackRow.className = "feedback-row";

    const usefulButton = document.createElement("button");
    usefulButton.className = "feedback-btn useful";
    usefulButton.textContent = "[ USEFUL ]";

    const notUsefulButton = document.createElement("button");
    notUsefulButton.className = "feedback-btn not-useful";
    notUsefulButton.textContent = "[ NOT USEFUL ]";

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

    message.textContent = "SCANNING ACTIVITY DATA...";
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
            message.textContent = `${data.count} DOMAINS • ${(data.ranking_method||'WEIGHTED').toUpperCase().replace('_', ' ')}`;
        } else {
            message.textContent = "NO ACTIVITY DATA YET • START BROWSING TO COLLECT DATA";
        }

        if (data.recommendations && Array.isArray(data.recommendations)) {
            data.recommendations.forEach((item, index) => {
                container.appendChild(createRecommendation(item, index));
            });
        }
    } catch (error) {
        message.textContent = "CONNECTION FAILED • CHECK API AT 127.0.0.1:8000";
        message.style.color = "#ff0040";
        console.error("Asterion recommendations error:", error);
    } finally {
        refreshButton.disabled = false;
        checkBackendConnection();
    }
}

document.getElementById("refresh").addEventListener("click", loadRecommendations);

checkBackendConnection();
showCurrentTab();
loadRecommendations();
