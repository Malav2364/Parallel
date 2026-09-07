"""Compose a conversational answer to a GitHub query -- LLM-free.

Sibling of ``app/briefing/compose.py``, but for the ``/process`` loop rather
than the arrival card: the chat surface renders only the ``message`` string, so
the answer has to carry the PRs inline. Same signal shape as the briefing
(``kind`` + ``payload``); deterministic, pure, singular/plural-correct.
"""


def _line(signal: dict) -> str:
    payload = signal.get("payload") or {}
    repo = payload.get("repo")
    number = payload.get("number")
    title = payload.get("title") or "Untitled"
    if repo and number:
        return f"• {repo} #{number} — {title}"
    if repo:
        return f"• {repo} — {title}"
    return f"• {title}"


def compose_github_reply(signals: list[dict], connected: bool) -> str:
    """A warm, first-person answer to a "what's on GitHub?" question.

    ``connected=False`` (the connector is off or the user hasn't linked GitHub)
    yields the same honest prompt the briefing uses -- never a fabricated
    "all caught up". Otherwise the reply names the PRs so the answer stands on
    its own in the chat transcript.
    """

    if not connected:
        return (
            "GitHub isn't connected yet — link it and I can keep an eye on "
            "your pull requests."
        )

    reviews = [s for s in signals if s.get("kind") == "review_request"]
    mine = [s for s in signals if s.get("kind") == "my_pr"]

    if not reviews and not mine:
        return "You're all caught up — nothing on GitHub needs you right now."

    blocks: list[str] = []

    if reviews:
        noun = "PR is" if len(reviews) == 1 else "PRs are"
        header = f"{len(reviews)} {noun} waiting on your review:"
        blocks.append("\n".join([header, *(_line(s) for s in reviews)]))

    if mine:
        noun = "PR" if len(mine) == 1 else "PRs"
        header = f"You have {len(mine)} open {noun}:"
        blocks.append("\n".join([header, *(_line(s) for s in mine)]))

    return "\n\n".join(blocks)
