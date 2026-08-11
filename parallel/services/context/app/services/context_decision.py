from google import genai

from app.core.config import settings
from app.schemas import ContextDecision
from app.services.context_extractor import ContextExtraction


class ContextDecisionEngine:
    """Evaluate context proposals without executing downstream actions."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def evaluate(
        self,
        user_input: str,
        current_context: dict,
        extraction: ContextExtraction,
    ) -> ContextDecision:
        prompt = f"""
You are the decision component of PIOS, a Personal Intelligence Operating
System.

Determine whether the user's message represents something PIOS should react
to.

Current context:
{current_context}

User message:
{user_input}

Extracted current-state updates:
{extraction.updates}

Rules:
1. Ignore temporary everyday events that do not affect long-term
   personalization.
2. Return every meaningful, independently identifiable signal in the signals
   array. One message may contain a life_change and a project signal.
3. Use signal type interest for a simple interest that does not justify a
   goal, project, habit, or Space.
4. Use signal type context_update for durable information that should update
   the user's current context.
5. Use signal type goal for an explicit goal.
6. Use signal type habit for an explicit habit or behavior-change intention.
7. Use signal type project for an active initiative requiring sustained work.
8. Use signal type life_change for a significant life transition.
9. Each signal must include a concise description and significance between 0
   and 1. Include name only when the signal has a meaningful name.
10. Choose exactly one action for the next executable step.
11. Use action create_project only when the user is explicitly trying to
    accomplish or build an ongoing project.
12. Use action update_context for durable context or meaningful interests
    that should be observed but do not justify creating an object.
13. Use action none for temporary events with no durable implication.
14. Do not create a project for a vague interest, casual idea, or topic
    mention.
15. Do not create a Space merely because a topic was mentioned once.
16. When action is create_project, provide concise project_name and
    project_description based only on the user's message.
17. When a project represents a significant long-term initiative, ongoing
    professional activity, business, career transition, or major life area,
    it should normally have a dedicated Space.
18. When action is create_project and the project is a significant ongoing
    initiative, provide space_candidate using the project name.
19. Do not leave space_candidate empty for a significant project unless there
    is a clear reason why a dedicated Space would be inappropriate.
20. A Space represents a persistent area of the user's life or work, while a
    Project represents a specific initiative within that area.
21. Do not create a Space merely because a topic was mentioned once. For a
    casual interest, leave space_candidate empty.
22. Do not invent information that is not supported by the user's message.
23. Do not return a decision field. The signals array replaces the old single
    decision field.

Examples:
- "I'm starting an AI startup" means project plus Space.
- "I'm building the landing page for my startup" refers to an existing
  project and existing Space.
- "I might learn photography someday" means interest with no Space.
- "I want to seriously learn photography and practice every weekend" means a
  goal or habit and may justify a Photography Space.

Return the signals, one action, and reason.
"""

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ContextDecision.model_json_schema(),
            },
        )

        return ContextDecision.model_validate_json(response.text or "{}")
