"""Deterministic idempotency keys for action execution.

Retries and double-taps of the same logical action (same user, same reminder
title and time) must not create duplicates. Hashing the action's natural key
yields a stable token we can send downstream and log against, so the same
request always maps to the same key regardless of how many times it is
replayed.
"""

import hashlib


def build_key(user_id: str, action: str, *parts: str | None) -> str:
    """Return a stable idempotency key for ``action`` and its natural key.

    ``parts`` are the fields that make the action unique (e.g. a reminder's
    title and scheduled time). They are normalised so trivial differences in
    whitespace or casing still collapse to the same key.
    """

    normalised = [(part or "").strip().casefold() for part in parts]
    canonical = "|".join([user_id, action, *normalised])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
