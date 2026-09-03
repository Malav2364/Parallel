"""Compose the twin's GitHub briefing from stored connector signals -- LLM-free.

The ``github`` connector stores timestamped signals (PRs awaiting the user's
review, and the user's own open PRs). :func:`build_briefing` reads that raw list
back into the shape the ``/briefing`` endpoint returns: split + counted items
plus one warm, first-person sentence.

Deterministic and pure (mirrors ``app/nlu/compose.py``): no clock, no I/O, no
model. Every phrase is singular/plural-correct so the digest reads naturally.
"""


def build_briefing(signals: list[dict], connected: bool) -> dict:
    """Turn raw github signals into the briefing response dict.

    ``signals`` is the github ``/signals`` list (newest-first); each carries a
    ``kind`` (``review_request`` / ``my_pr``) and a ``payload``. ``connected``
    tells "not connected" apart from "connected but all caught up".
    """

    reviews = [s for s in signals if s.get("kind") == "review_request"]
    mine = [s for s in signals if s.get("kind") == "my_pr"]

    return {
        "connected": connected,
        "review_requests": len(reviews),
        "my_open_prs": len(mine),
        "message": _message(connected, len(reviews), len(mine)),
        "review_requests_items": [_item(s) for s in reviews],
        "my_pr_items": [_item(s) for s in mine],
    }


def _item(signal: dict) -> dict:
    """The compact, UI-ready slice of a signal's payload (order preserved)."""

    payload = signal.get("payload") or {}
    return {
        "repo": payload.get("repo"),
        "number": payload.get("number"),
        "title": payload.get("title"),
        "url": payload.get("url"),
    }


def _message(connected: bool, reviews: int, mine: int) -> str:
    if not connected:
        return "Connect GitHub to see your pull requests."

    if reviews == 0 and mine == 0:
        return "You're all caught up — nothing on GitHub needs you right now."

    if reviews > 0:
        noun = "PR" if reviews == 1 else "PRs"
        sentence = f"{reviews} {noun} waiting on your review"
        if mine > 0:
            verb = "is" if mine == 1 else "are"
            return f"{sentence}, and {mine} of your own {verb} open."
        return f"{sentence}."

    # reviews == 0 and mine > 0
    verb = "is" if mine == 1 else "are"
    return f"No PRs need your review; {mine} of your own {verb} open."
