"""Tests for check_links.py: URL collection and the status check (no network)."""
from check_links import check, collect_urls


def test_collect_urls_nested_and_dedup():
    content = {
        "site": {"url": "https://fireunderice.org"},
        "video": {"url": "https://a.example/x"},
        "press": {"articles": [
            {"link": "https://b.example/y"},
            {"link": "https://a.example/x"},
            {"note": "not a url", "deep": ["http://c.example/z"]},
        ]},
    }
    assert collect_urls(content) == [
        "https://a.example/x",
        "https://b.example/y",
        "http://c.example/z",
    ]


def test_collect_skips_site_url():
    content = {
        "site": {"url": "https://fireunderice.org"},
        "tv": [{"url": "https://mediaset.example/v"}],
    }
    assert collect_urls(content) == ["https://mediaset.example/v"]


def test_check_falls_back_to_get():
    calls = []

    def fake_fetch(url, method):
        calls.append(method)
        return 405 if method == "HEAD" else 200

    assert check("https://a.example/", fake_fetch) == ("https://a.example/", 200)
    assert calls == ["HEAD", "GET"]


def test_check_reports_exception():
    def fake_fetch(url, method):
        raise TimeoutError("slow")

    assert check("https://a.example/", fake_fetch) == ("https://a.example/", "TimeoutError")
