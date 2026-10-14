import threading


def test_mixed_wordlist_threads_use_target_domain(checker, url_recorder):
    # Issue #29: email-format lines must not change the domain used for bare usernames.
    names = []
    for i in range(150):
        names.append(f"other{i}@example.org")
        names.append(f"bare{i}")

    threads = [threading.Thread(target=checker.check_url, args=(n,)) for n in names]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bare = [u for u in url_recorder.urls if "/personal/bare" in u]
    wrong = [u for u in bare if "_contoso_com/" not in u]
    assert len(bare) == 150
    assert wrong == []


def test_email_line_uses_its_own_domain(checker, url_recorder):
    checker.check_url("jsmith@example.org")

    assert len(url_recorder.urls) == 1
    assert "/personal/jsmith_example_org/" in url_recorder.urls[0]


def test_bare_username_after_email_line_uses_target_domain(checker, url_recorder):
    checker.check_url("jsmith@example.org")
    checker.check_url("bjones")

    assert "/personal/bjones_contoso_com/" in url_recorder.urls[1]
