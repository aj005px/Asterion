const TIMER_KEY = "asterion_active_tab";
const SESSION_KEY = "asterion_session_id";

async function getSessionId() {
    const data = await chrome.storage.session.get(SESSION_KEY);

    if (data[SESSION_KEY]) {
        return data[SESSION_KEY];
    }

    const sessionId = crypto.randomUUID();

    await chrome.storage.session.set({
        [SESSION_KEY]: sessionId
    });

    return sessionId;
}
async function getActiveTabState() {
    const data = await chrome.storage.session.get(TIMER_KEY);
    return data[TIMER_KEY];
}

async function setActiveTabState(state) {
    await chrome.storage.session.set({
        [TIMER_KEY]: state
    });
}

async function saveDuration(state, endTime) {
    const durationSeconds = (endTime - state.startedAt) / 1000;

    if (durationSeconds <= 0 || !state.url) {
        return;
    }

    const response = await fetch(
        "http://127.0.0.1:8000/tab/duration",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: state.url,
                tab_id: state.tabId,
                session_id: state.sessionId,
                duration_seconds: durationSeconds
            })
        }
    );

    if (!response.ok) {
        throw new Error(`Duration save failed: HTTP ${response.status}`);
    }

    console.log(
        `Asterion saved ${durationSeconds.toFixed(1)} seconds:`,
        state.url
    );
}

async function finishTrackedTab(tabId, endTime) {
    const state = await getActiveTabState();

    if (!state || state.tabId !== tabId) {
        return;
    }

    await chrome.storage.session.remove(TIMER_KEY);
    await saveDuration(state, endTime);
}

async function activateUrl(tabId, url, startedAt = Date.now()) {
    const sessionId = await getSessionId();

    const response = await fetch(
        "http://127.0.0.1:8000/tab/activate",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url,
                tab_id: tabId,
                session_id: sessionId
            })
        }
    );

    if (!response.ok) {
        throw new Error(`Activation failed: HTTP ${response.status}`);
    }

    await setActiveTabState({
        tabId,
        url,
        startedAt,
        sessionId
    });

    console.log("Asterion tracking:", url);
}

// Track switching between tabs.
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const now = Date.now();
        const previous = await getActiveTabState();

        if (previous && previous.tabId !== activeInfo.tabId) {
            await finishTrackedTab(previous.tabId, now);
        }

        const tab = await chrome.tabs.get(activeInfo.tabId);

        if (!tab.url || !tab.url.startsWith("http")) {
            await chrome.storage.session.remove(TIMER_KEY);
            return;
        }

        await activateUrl(activeInfo.tabId, tab.url, now);
    } catch (error) {
        console.error("Asterion activation error:", error);
    }
});

// Track navigation within the currently active tab.
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status !== "complete" || !tab.url) {
        return;
    }

    if (!tab.url.startsWith("http")) {
        return;
    }

    try {
        const state = await getActiveTabState();

        if (!state || state.tabId !== tabId || state.url === tab.url) {
            return;
        }

        const now = Date.now();

        await finishTrackedTab(tabId, now);
        await activateUrl(tabId, tab.url, now);

        console.log("Asterion tracked navigation:", tab.url);
    } catch (error) {
        console.error("Asterion navigation error:", error);
    }
});

// Save the duration when a tracked tab closes.
chrome.tabs.onRemoved.addListener(async (tabId) => {
    try {
        await finishTrackedTab(tabId, Date.now());
        console.log("Asterion finished tracking closed tab:", tabId);
    } catch (error) {
        console.error("Asterion tab-close error:", error);
    }
});
