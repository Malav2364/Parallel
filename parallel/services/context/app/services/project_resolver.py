from google import genai

from app.clients.projects_client import ProjectsClient
from app.core.config import settings
from app.schemas.project_resolution import ProjectResolution


class ProjectResolver:
    def __init__(
        self,
        projects_client: ProjectsClient,
    ):
        self.projects_client = projects_client

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    def resolve(
        self,
        user_id: str,
        user_input: str,
    ) -> ProjectResolution:
        projects = self.projects_client.list_projects(
            user_id,
        )

        if not projects:
            return ProjectResolution(
                matched=False,
                confidence=1.0,
                reason="The user has no existing projects.",
            )

        prompt = f"""
You are the project resolution component of PIOS.

Determine whether the user's message refers to one
of the user's existing projects.

Existing projects:
{projects}

User message:
{user_input}

Rules:

1. Match the user's message to an existing project when
   the message is meaningfully related to that project's
   objective, description, current focus, latest activity,
   or known terminology.

2. Do not require the user to explicitly mention the
   project name.

3. Infer reasonable semantic relationships.

4. For example, a project named "AI Startup" with a
   current focus of "Payment integration" should match
   messages about:
   - payment integration
   - Stripe
   - checkout
   - payment gateway
   - billing
   - subscriptions
   - fixing payment bugs

5. Do not match merely because a generic word overlaps.

6. If two or more projects are plausible matches and the
   message does not provide enough evidence to distinguish
   them, return matched=false.

7. If a message contains multiple intents, separate project
   activity from broader context updates. Match the project that
   the concrete work or progress belongs to.

8. Do not treat a separate future focus, study plan, goal, or
   life-area mention as a competing project match unless the
   message describes concrete activity within that project too.

9. For example, "I completed the checkout page of my AI product
   and now I will study for MBA" should match the AI product
   project for the checkout activity. The MBA portion is a
   separate context or goal update.

10. If there is no meaningful relationship, return matched=false.

11. Never invent a project ID.

12. Confidence must be between 0 and 1.

13. Prefer an existing project when the semantic relationship
    is strong, even if the project name is not explicitly
    mentioned.
"""

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": (ProjectResolution.model_json_schema()),
            },
        )

        result = ProjectResolution.model_validate_json(
            response.text,
        )

        # Safety check. Gemini should never be allowed to
        # manufacture an arbitrary project ID.
        if result.matched:
            valid_ids = {project["id"] for project in projects}

            if result.project_id not in valid_ids:
                return ProjectResolution(
                    matched=False,
                    confidence=0.0,
                    reason="Resolver returned an invalid project ID.",
                )

        return result
