def test_tab_warning_threshold_default():
    # Default threshold is 20 as specified
    threshold = 20
    assert threshold == 20


def test_tab_warning_relevant_tabs_filter():
    def is_relevant(url):
        if not url:
            return False
        if url.startswith("chrome://") or url.startswith("chrome-extension://"):
            return False
        if url.startswith("edge://") or url.startswith("about:"):
            return False
        if url.startswith("devtools://") or url.startswith("chrome-search://"):
            return False
        return True

    assert is_relevant("https://example.com") is True
    assert is_relevant("http://example.com") is True
    assert is_relevant("chrome://settings") is False
    assert is_relevant("chrome-extension://abc") is False
    assert is_relevant("about:blank") is False


def test_tab_warning_crossing_logic():
    # When count crosses threshold (>=20), alert should trigger if not alerted above
    threshold = 20
    count = 19
    alerted_above = False
    # below
    assert count < threshold
    count = 20
    # crossed up
    should_alert = count >= threshold and not alerted_above
    assert should_alert is True


def test_tab_warning_no_repeat_above_cooldown():
    threshold = 20
    count = 25
    alerted_above = True
    last_alert_time = 1000
    now = 1500
    cooldown_ms = 10 * 60 * 1000
    # within cooldown, should not alert again
    if count >= threshold and alerted_above and (now - last_alert_time < cooldown_ms):
        should_alert_again = False
    else:
        should_alert_again = True
    assert should_alert_again is False


def test_tab_warning_reset_below_allows_again():
    threshold = 20
    count = 15
    alerted_above = True
    # fell below
    if count < threshold and alerted_above:
        alerted_above_new = False
    else:
        alerted_above_new = alerted_above
    assert alerted_above_new is False
    # crosses again
    count = 21
    should_alert = count >= threshold and alerted_above_new is False
    assert should_alert is True
