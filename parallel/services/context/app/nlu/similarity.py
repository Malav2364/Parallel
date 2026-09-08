"""Tier-2 similarity core: pure-Python cosine ranking, no I/O.

The semantic project resolver embeds a user's projects and their message into
vectors elsewhere (via the embedding client); this module turns those vectors
into a decision. Kept dependency-free (no numpy) and side-effect-free so it is
trivially unit-testable and cheap to call on the request path.
"""

import math


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors, in ``[-1.0, 1.0]``.

    Returns ``0.0`` when either vector is all zeros (its direction is
    undefined) so callers never divide by zero or leak a NaN into a ranking.
    Raises ``ValueError`` if the vectors differ in length (e.g. a stale cache
    row from a different embedding model) rather than silently truncating to a
    misleading score -- the caller treats that as a miss and defers.
    """

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)


def rank(
    query: list[float],
    candidates: list[tuple[str, list[float]]],
) -> list[tuple[str, float]]:
    """Score each ``(id, vector)`` candidate against ``query``, best first.

    Ties preserve input order (Python's sort is stable), so the ranking is
    deterministic when two candidates score identically.
    """

    scored = [(cid, cosine(query, vec)) for cid, vec in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def decide(
    ranked: list[tuple[str, float]],
    *,
    threshold: float,
    margin: float,
) -> tuple[str | None, float]:
    """Pick a confident, unambiguous winner from a ranking, or decline.

    Returns ``(id, score)`` only when the top candidate clears ``threshold``
    AND leads the runner-up by at least ``margin`` -- a clear winner. Anything
    short of that returns ``(None, top_score)`` so the caller defers to a later
    tier rather than guessing (never silently wrong). The top score is always
    reported back for logging/telemetry. An empty ranking returns ``(None,
    0.0)``.
    """

    if not ranked:
        return None, 0.0

    top_id, top_score = ranked[0]
    if top_score < threshold:
        return None, top_score

    # A lone candidate has nothing to be confused with (runner-up 0.0), so a
    # clear-of-threshold single project resolves.
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_score - second_score < margin:
        return None, top_score

    return top_id, top_score
