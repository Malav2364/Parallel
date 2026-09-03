"""build_briefing composes a deterministic, singular/plural-correct digest.

Pure-function tests in the house style (``tests/test_compose.py``): exact-string
assertions, no clock and no I/O. Signal fixtures mirror the github ``/signals``
shape -- a ``kind`` plus a ``payload`` -- carrying only the fields the composer
reads.
"""

from app.briefing.compose import build_briefing


def _signal(kind: str, **payload) -> dict:
    return {"kind": kind, "payload": payload}


def _review(**payload) -> dict:
    return _signal("review_request", **payload)


def _mine(**payload) -> dict:
    return _signal("my_pr", **payload)


def test_reviews_and_mine_are_counted_and_pluralised() -> None:
    briefing = build_briefing(
        signals=[_review(), _review(), _mine(), _mine(), _mine()],
        connected=True,
    )

    assert briefing["review_requests"] == 2
    assert briefing["my_open_prs"] == 3
    assert (
        briefing["message"]
        == "2 PRs waiting on your review, and 3 of your own are open."
    )


def test_single_review_and_single_mine_read_singular() -> None:
    briefing = build_briefing(signals=[_review(), _mine()], connected=True)

    assert (
        briefing["message"] == "1 PR waiting on your review, and 1 of your own is open."
    )


def test_reviews_only_has_no_trailing_clause() -> None:
    briefing = build_briefing(signals=[_review(), _review()], connected=True)

    assert briefing["message"] == "2 PRs waiting on your review."


def test_mine_only_when_no_reviews_is_singular_and_plural_correct() -> None:
    many = build_briefing(signals=[_mine(), _mine()], connected=True)
    assert many["message"] == "No PRs need your review; 2 of your own are open."

    one = build_briefing(signals=[_mine()], connected=True)
    assert one["message"] == "No PRs need your review; 1 of your own is open."


def test_connected_but_empty_is_all_caught_up() -> None:
    briefing = build_briefing(signals=[], connected=True)

    assert briefing["review_requests"] == 0
    assert briefing["my_open_prs"] == 0
    assert (
        briefing["message"]
        == "You're all caught up — nothing on GitHub needs you right now."
    )


def test_not_connected_prompts_to_connect_with_zero_counts() -> None:
    briefing = build_briefing(signals=[], connected=False)

    assert briefing["connected"] is False
    assert briefing["review_requests"] == 0
    assert briefing["my_open_prs"] == 0
    assert briefing["review_requests_items"] == []
    assert briefing["my_pr_items"] == []
    assert briefing["message"] == "Connect GitHub to see your pull requests."


def test_items_map_payload_fields_split_by_kind_preserving_order() -> None:
    signals = [
        _review(
            repo="me/api",
            number=12,
            title="Fix bug",
            url="https://x/12",
            author="a",
        ),
        _mine(
            repo="me/web",
            number=7,
            title="Add page",
            url="https://x/7",
            author="me",
        ),
        _review(
            repo="me/api",
            number=13,
            title="Refactor",
            url="https://x/13",
            author="b",
        ),
    ]

    briefing = build_briefing(signals=signals, connected=True)

    # Split by kind, order preserved, only the four UI fields kept (no author).
    assert briefing["review_requests_items"] == [
        {"repo": "me/api", "number": 12, "title": "Fix bug", "url": "https://x/12"},
        {"repo": "me/api", "number": 13, "title": "Refactor", "url": "https://x/13"},
    ]
    assert briefing["my_pr_items"] == [
        {"repo": "me/web", "number": 7, "title": "Add page", "url": "https://x/7"},
    ]
