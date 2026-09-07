"""Recognise a read-only GitHub query in the conversation loop -- LLM-free.

The twin already reads GitHub for its arrival briefing; this lets the same
signals answer a mid-conversation question ("what's waiting on my review?",
"any open PRs of mine?"). :func:`is_github_query` is a deterministic Tier-1
recogniser, sibling of ``app/nlu/rules.py``: it only fires on a clear GitHub
*question*, so a create-intent ("remind me to review the PR") is claimed by the
reminder proposer first and never mistaken for a lookup.

Conservative by design. An anchor alone ("the PR") is not enough; it must pair
with a query framing ("any"/"what"/"show"), OR the utterance must carry a strong
standalone phrase ("waiting on my review", "my open PRs") that is unambiguously
a GitHub lookup on its own.
"""

import re

# A GitHub-domain term: the platform, or the pull-request vocabulary.
_ANCHOR = re.compile(
    r"\b(?:github|pull\s*requests?|prs?|review\s*requests?|code\s*reviews?)\b",
    re.IGNORECASE,
)

# Query framing that turns an anchor into a lookup ("any PRs?", "show my PRs").
_FRAMING = re.compile(
    r"\b(?:what'?s?|which|any|anything|show|list|check|see|how\s+many"
    r"|are\s+there|do\s+i\s+have|got|status|open|waiting|pending|need)\b",
    re.IGNORECASE,
)

# Phrases that are a GitHub lookup by themselves, no framing word required.
_STANDALONE = re.compile(
    r"(?:waiting\s+on\s+(?:my|me)\b|(?:my\s+)?(?:pending|awaiting)\s+reviews?"
    r"|need(?:s|ing)?\s+(?:my\s+)?review|my\s+open\s+(?:prs?|pull\s*requests?)"
    r"|open\s+pull\s*requests?)",
    re.IGNORECASE,
)


def is_github_query(text: str) -> bool:
    """True when the utterance is a read-only question about GitHub PRs."""

    if _STANDALONE.search(text):
        return True
    return bool(_ANCHOR.search(text) and _FRAMING.search(text))
