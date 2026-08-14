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
2. Only extract activity that belongs specifically to the
   resolved project shown above.
3. latest_activity must summarize something the user actually
   did, changed, completed, started, or encountered within the
   resolved project.
4. current_focus must describe what the user is currently
   working on within the resolved project.
5. Do not treat the user's broader personal focus, next activity,
   study plan, life area, habit, career change, or unrelated goal
   as the project's current_focus.
6. If the message mentions another goal or life area that is
   unrelated to the resolved project, ignore it for project
   activity.
7. If the user gives completed project work but then says they
   will switch to an unrelated focus, extract only latest_activity
   for the completed project work. Omit current_focus.
8. Example: if the resolved project is the user's AI product and
   the user says "I completed the checkout page of my AI product
   and now I will study for MBA", extract only:
   latest_activity = "Completed the checkout page".
9. Do not invent tasks, technologies, deadlines, or outcomes.
10. If the message contains no useful project activity,
    omit current_focus and latest_activity.
11. Keep both fields concise.
12. Confidence must be between 0 and 1.

Return JSON matching the requested schema.
"""

        response = self.client.models.generate_content(
            model=settings.CONTEXT_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": (ProjectActivity.model_json_schema()),
            },
        )

        return ProjectActivity.model_validate_json(
            response.text,
        )
