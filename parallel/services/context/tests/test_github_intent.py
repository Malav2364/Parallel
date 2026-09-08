"""is_github_query fires on GitHub lookups, declines create-intents and noise."""

import pytest

from app.nlu.github_intent import is_github_query


@pytest.mark.parametrize(
    "text",
    [
        "what's waiting on my review?",
        "any PRs for me to review?",
        "show me my open PRs",
        "any open pull requests?",
        "do I have any pull requests waiting?",
        "how many PRs need my review",
        "check github",
        "what's the status of my pull requests",
        "anything on github?",
        "my pending reviews",
    ],
)
def test_recognises_github_queries(text: str) -> None:
    assert is_github_query(text) is True


@pytest.mark.parametrize(
    "text",
    [
        # Create-intents whose framing is unambiguous stay out of the lookup
        # path at the recogniser level.
        "remind me to review the PR tomorrow at 9am",
        "my goal is to review more pull requests",
        # Unrelated conversation.
        "remind me to call mom",
        "help me build a habit of reading",
        "what's the weather today",
        "I want to meditate every day",
        "the review of the restaurant was great",
    ],
)
def test_declines_non_queries(text: str) -> None:
    assert is_github_query(text) is False


def test_recogniser_alone_cannot_tell_create_from_lookup() -> None:
    """The bare recogniser is deliberately liberal: "open a pull request"
    (create) and "open pull requests" (lookup) are indistinguishable to it, so
    it fires on both. Precedence over create-intents is the /process endpoint's
    job -- it only consults is_github_query when propose() finds no create-intent
    (see test_process_endpoint's precedence test). Pinning that liberal contract
    here documents why the endpoint gate, not a regex arms race, owns the split.
    """

    assert is_github_query("remind me to open a pull request") is True
