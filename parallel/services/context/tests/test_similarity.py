"""Tier-2 similarity core tests: cosine, ranking, and the decision gate.

Uses hand-built synthetic vectors so the assertions never depend on a real
embedding model or its magnitudes -- only on the pure math and the gating
policy (threshold + clear-winner margin).
"""

import pytest

from app.nlu.similarity import cosine, decide, rank


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ([1.0, 0.0, 0.0], [1.0, 0.0, 0.0], 1.0),  # identical direction
        ([1.0, 0.0], [0.0, 1.0], 0.0),  # orthogonal
        ([1.0, 0.0], [-1.0, 0.0], -1.0),  # opposite
        ([2.0, 0.0], [5.0, 0.0], 1.0),  # magnitude-invariant
        ([0.0, 0.0], [1.0, 1.0], 0.0),  # zero vector -> guarded to 0.0
    ],
)
def test_cosine(a: list[float], b: list[float], expected: float) -> None:
    assert cosine(a, b) == pytest.approx(expected)


def test_cosine_length_mismatch_raises() -> None:
    # A dimension mismatch is never silently scored -- it raises so the caller
    # can treat it as a miss and defer to a later tier.
    with pytest.raises(ValueError):
        cosine([1.0, 0.0], [1.0, 0.0, 0.0])


def test_rank_orders_by_similarity_descending() -> None:
    query = [1.0, 0.0]
    candidates = [
        ("far", [0.0, 1.0]),  # orthogonal -> 0.0
        ("near", [1.0, 0.1]),  # closest to query
        ("mid", [1.0, 1.0]),  # 45 degrees -> ~0.707
    ]

    ranked = rank(query, candidates)

    assert [cid for cid, _ in ranked] == ["near", "mid", "far"]
    assert ranked[0][1] > ranked[1][1] > ranked[2][1]


def test_decide_clear_winner_matches() -> None:
    ranked = [("p1", 0.90), ("p2", 0.40)]

    chosen, score = decide(ranked, threshold=0.78, margin=0.06)

    assert chosen == "p1"
    assert score == pytest.approx(0.90)


def test_decide_below_threshold_declines() -> None:
    # Leads clearly, but nothing is similar enough to act on.
    ranked = [("p1", 0.50), ("p2", 0.10)]

    chosen, score = decide(ranked, threshold=0.78, margin=0.06)

    assert chosen is None
    assert score == pytest.approx(0.50)


def test_decide_ambiguous_top_two_declines() -> None:
    # Both clear the threshold but sit within the margin: too close to call, so
    # defer rather than guess.
    ranked = [("p1", 0.83), ("p2", 0.80)]

    chosen, score = decide(ranked, threshold=0.78, margin=0.06)

    assert chosen is None
    assert score == pytest.approx(0.83)


def test_decide_single_candidate_clearing_threshold_matches() -> None:
    # One project, nothing to confuse it with: a clear-of-threshold score wins.
    ranked = [("only", 0.81)]

    chosen, score = decide(ranked, threshold=0.78, margin=0.06)

    assert chosen == "only"
    assert score == pytest.approx(0.81)


def test_decide_empty_ranking_declines() -> None:
    chosen, score = decide([], threshold=0.78, margin=0.06)

    assert chosen is None
    assert score == 0.0
