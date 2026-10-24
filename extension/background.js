const TIMER_KEY = "asterion_active_tab";
const SESSION_KEY = "asterion_session_id";

// Tab warning configuration
const TAB_WARNING_THRESHOLD = 20;
const TAB_WARNING_COOLDOWN_MS = 10 * 60 * 1000; // 10 minutes
const TAB_WARNING_LAST_ALERT_KEY = "asterion_tab_warning_last_alert";
const TAB_WARNING_ALERTED_ABOVE_KEY = "asterion_tab_warning_alerted_above";

function isRelevantUrl(url) {
    if (!url) {
        return false;
    }
    if (url.startsWith("chrome://") || url.startsWith("chrome-extension://")) {
        return false;
    }
    if (url.startsWith("edge://") || url.startsWith("about:")) {
        return false;
    }
    if (url.startsWith("devtools://") || url.startsWith("chrome-search://")) {
        return false;
    }
    // Count normal http/https pages and others that are browsable tabs
    return true;
}

async function countRelevantTabs() {
    try {
        const windows = await chrome.windows.getAll({ populate: true });
        let count = 0;
        for (const win of windows) {
            if (!win.tabs) {
                continue;
            }
            for (const tab of win.tabs) {
                if (isRelevantUrl(tab.url)) {
                    count += 1;
                }
            }
        }
        return count;
    } catch (error) {
        console.error("Asterion tab count error:", error);
        return 0;
    }
}

async function updateTabWarningBadge(count) {
    try {
        if (count >= TAB_WARNING_THRESHOLD) {
            await chrome.action.setBadgeText({ text: String(count) });
            await chrome.action.setBadgeBackgroundColor({ color: "#800000" });
        } else {
            await chrome.action.setBadgeText({ text: "" });
        }
    } catch (error) {
        console.error("Asterion badge error:", error);
    }
}

async function checkAndWarnAboutTabs() {
    const count = await countRelevantTabs();
    await updateTabWarningBadge(count);

    const now = Date.now();
    const storage = await chrome.storage.local.get([
        TAB_WARNING_LAST_ALERT_KEY,
        TAB_WARNING_ALERTED_ABOVE_KEY
    ]);

    const lastAlert = storage[TAB_WARNING_LAST_ALERT_KEY] || 0;
    const alertedAbove = storage[TAB_WARNING_ALERTED_ABOVE_KEY] === true;

    if (count >= TAB_WARNING_THRESHOLD) {
        // If already alerted above and within cooldown, do not spam
        if (alertedAbove && now - lastAlert < TAB_WARNING_COOLDOWN_MS) {
            return;
        }
        // If not currently alerted above (crossed from below) or cooldown passed, alert
        if (!alertedAbove || now - lastAlert >= TAB_WARNING_COOLDOWN_MS) {
            try {
                await chrome.notifications.create({
                    type: "basic",
                    iconUrl: "icons/icon128.png",
                    title: "Asterion",
                    message: `You have ${count} open tabs. Review tab priorities.`
                });
                await chrome.storage.local.set({
                    [TAB_WARNING_LAST_ALERT_KEY]: now,
                    [TAB_WARNING_ALERTED_ABOVE_KEY]: true
                });
            } catch (error) {
                console.error("Asterion notification error:", error);
            }
        }
    } else {
        // Fell below threshold - allow alert again later if crosses up
        if (alertedAbove) {
            await chrome.storage.local.set({
                [TAB_WARNING_ALERTED_ABOVE_KEY]: false
            });
        }
    }
}

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

    try {
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
    } catch (error) {
        console.error("Asterion save duration error:", error);
    }
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

    try {
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
    } catch (error) {
        console.error("Asterion activation error:", error);
    }
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
    // Check tab count after changes
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
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
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
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
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
    }
});

chrome.tabs.onCreated.addListener(async () => {
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
    }
});

chrome.windows.onRemoved.addListener(async () => {
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
    }
});

// When notification is clicked, try to open popup context by focusing window
chrome.notifications.onClicked.addListener(async (notificationId) => {
    try {
        // Chrome cannot programmatically open action popup in most cases; focus window as supported action
        const windows = await chrome.windows.getAll({ windowTypes: ["normal"] });
        if (windows.length > 0) {
            await chrome.windows.update(windows[0].id, { focused: true });
        }
    } catch (error) {
        console.error("Asterion notification click error:", error);
    }
});

// On service worker startup/install, do not spam alerts just because count already high
// Only set badge
chrome.runtime.onInstalled.addListener(async () => {
    try {
        const count = await countRelevantTabs();
        await updateTabWarningBadge(count);
    } catch (e) {
        console.error(e);
    }
});

chrome.runtime.onStartup.addListener(async () => {
    try {
        const count = await countRelevantTabs();
        await updateTabWarningBadge(count);
    } catch (e) {
        console.error(e);
    }
});

// Periodic check to catch cases if events missed (lightweight)
setInterval(async () => {
    try {
        await checkAndWarnAboutTabs();
    } catch (e) {
        console.error(e);
    }
}, 60000);
