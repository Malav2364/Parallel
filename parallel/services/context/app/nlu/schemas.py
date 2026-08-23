"""NLU cascade primitives.

Every understanding tier (structured UI, deterministic rules, local NLU,
and the LLM fallback) emits a single :class:`ProposedAction`. This lets the
pipeline gate execution on a uniform confidence signal regardless of which
tier produced the proposal.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.decision import ActionType

ProposalSource = Literal["ui", "rules", "nlu", "llm"]

# Confidence bands that drive the execution gate.
HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.5

ConfidenceBand = Literal["high", "medium", "low"]


def confidence_band(score: float) -> ConfidenceBand:
    if score >= HIGH_CONFIDENCE:
        return "high"

    if score >= MEDIUM_CONFIDENCE:
        return "medium"

    return "low"


class ProposedAction(BaseModel):
    """A single action proposed by one tier of the understanding cascade."""

    action: ActionType
    source: ProposalSource
    confidence: float = Field(ge=0, le=1)

    # Structured, per-action slots resolved by the tier (title, dates, ...).
    slots: dict[str, Any] = Field(default_factory=dict)

    # Human-readable justification, retained for logging and debugging.
    reason: str | None = None

    @property
    def band(self) -> ConfidenceBand:
        return confidence_band(self.confidence)

    @property
    def is_executable(self) -> bool:
        """High confidence and a real action -> safe to auto-execute."""
        return self.band == "high" and self.action != "none"
