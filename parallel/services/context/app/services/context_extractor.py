from google import genai

from app.core.config import settings
from app.schemas.extraction import ContextExtraction

__all__ = ["ContextExtraction", "ContextExtractor", "normalize_extraction_updates"]


def normalize_extraction_updates(updates: dict, current_context: dict) -> dict:
    """Fold freshly-extracted goals into ``goals_to_add`` and drop the
    service-owned ``projects`` key.

    Shared by the standalone ``ContextExtractor`` and the merged
    ``UnderstandingEngine`` so both normalize identical whether the extraction
    came from its own call or the combined understanding call.
    """
    if "goals" in updates and "goals_to_add" not in updates:
        existing_goals = current_context.get("goals", [])
        extracted_goals = updates.pop("goals")

        existing_normalized = {
            goal.strip().lower() for goal in existing_goals if isinstance(goal, str)
        }
        new_goals = [
            goal
            for goal in extracted_goals
            if isinstance(goal, str) and goal.strip().lower() not in existing_normalized
        ]
        if new_goals:
            updates["goals_to_add"] = new_goals

    updates.pop("projects", None)
    return updates


class ContextExtractor:
    """Extract durable user context from natural-language input."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract(
        self,
        user_input: str,
        current_context: dict,
    ) -> ContextExtraction:
        prompt = f"""
You are the context extraction component of a Personal Intelligence Operating
System (PIOS).

Identify meaningful, durable, user-specific information from the user's
message.

Current user context:
{current_context}

User message:
{user_input}

When extracting goals:
- If the user introduces a new goal, return it under
  "goals_to_add".
- "goals_to_add" must contain ONLY goals introduced by the
  current message.
- Never return the user's complete existing goal list.
- Never copy goals from "Current user context" into
  "goals_to_add".
- If the user does not introduce a new goal, do not include
  "goals_to_add".
- If an existing goal is discussed or updated, represent that
  as an appropriate update rather than adding a duplicate.

  
Rules:
1. Extract only information supported by the message.
2. Never invent facts.
3. Do not treat temporary events as permanent user characteristics.
4. Focus on information useful for long-term personalization.
5. Identify changes to occupation, interests, goals, priorities, habits,
   preferences, projects, or important life circumstances when explicitly
   supported.
6. If the message contains no meaningful durable information, return an
   empty updates object.
7. Confidence must be between 0 and 1.
8. Extract only the user's current state.
9. Never create keys such as previous_*, old_*, former_*, historical_*, or
   similar historical fields.
10. Historical values are handled by the Context Service through change
    detection.
11. When the user explicitly describes a transition in their occupation,
    career, lifestyle, or major commitment, extract the new or current state.
12. Do not create previous_* fields for transitions.
13. Capture an explicit transition as a meaningful current-state field such
    as career_status or current_focus.
14. Do not infer a new occupation unless the user explicitly establishes it.
15. Do not store project progress, project status, completed tasks, or
    activity updates in the user's durable context. Those belong to the
    Project Activity layer.
16. Never return a top-level "projects" key. Existing projects are owned by
    the Projects Service, not user context.
"""

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ContextExtraction.model_json_schema(),
            },
        )

        result = ContextExtraction.model_validate_json(response.text or "{}")

        return ContextExtraction(
            updates=normalize_extraction_updates(result.updates, current_context),
            confidence=result.confidence,
            reasoning=result.reasoning,
        )
