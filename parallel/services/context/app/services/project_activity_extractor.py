from google import genai

from app.core.config import settings
from app.schemas.project_activity import ProjectActivity


class ProjectActivityExtractor:
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

    def extract(
        self,
        user_input: str,
        project: dict,
    ) -> ProjectActivity:
        prompt = f"""
You are the project activity extraction component of PIOS.

Existing project:
{project}

User message:
{user_input}

Determine whether the message contains useful information
about the user's activity within this project.

Rules:

1. Only extract information supported by the message.
2. latest_activity should summarize what the user actually
   did, changed, completed, started, or encountered.
3. current_focus should represent what the user appears to
   currently be working on.
4. Do not invent tasks, technologies, deadlines, or outcomes.
5. If the message contains no useful project activity,
   return null for the relevant fields.
6. Keep both fields concise.
7. Confidence must be between 0 and 1.

Return JSON matching the requested schema.
"""

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": (
                    ProjectActivity.model_json_schema()
                ),
            },
        )

        return ProjectActivity.model_validate_json(
            response.text,
        )