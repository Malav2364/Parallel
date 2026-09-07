"""compose_github_reply renders signals as a chat answer, degrading honestly."""

from app.nlu.github_reply import compose_github_reply


def _signal(kind: str, **payload) -> dict:
    return {"kind": kind, "payload": payload}


def test_not_connected_prompts_to_link_never_fabricates() -> None:
    reply = compose_github_reply(signals=[], connected=False)
    assert "isn't connected" in reply
    assert "caught up" not in reply


def test_connected_no_signals_reports_caught_up() -> None:
    reply = compose_github_reply(signals=[], connected=True)
    assert reply == "You're all caught up — nothing on GitHub needs you right now."


def test_review_and_own_prs_named_inline() -> None:
    signals = [
        _signal("review_request", repo="me/api", number=12, title="Fix auth"),
        _signal("review_request", repo="me/api", number=13, title="Add cache"),
        _signal("my_pr", repo="me/web", number=7, title="Dark mode"),
    ]
    reply = compose_github_reply(signals=signals, connected=True)
    assert "2 PRs are waiting on your review:" in reply
    assert "• me/api #12 — Fix auth" in reply
    assert "• me/api #13 — Add cache" in reply
    assert "You have 1 open PR:" in reply
    assert "• me/web #7 — Dark mode" in reply


def test_singular_review_grammar() -> None:
    signals = [_signal("review_request", repo="me/api", number=1, title="One")]
    reply = compose_github_reply(signals=signals, connected=True)
    assert "1 PR is waiting on your review:" in reply


def test_missing_payload_fields_do_not_crash() -> None:
    signals = [_signal("my_pr")]
    reply = compose_github_reply(signals=signals, connected=True)
    assert "You have 1 open PR:" in reply
    assert "• Untitled" in reply
