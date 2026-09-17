from collections.abc import Awaitable, Callable
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.clients.github_client import GithubClient
from app.clients.goals_client import GoalsClient
from app.clients.habits_client import HabitsClient
from app.clients.projects_client import ProjectsClient
from app.clients.reminders_client import RemindersClient
from app.clients.workspace_client import WorkspaceClient
from app.schemas.decision import ContextDecision
from app.services.idempotency import build_key
from app.services.reminder_datetime import ReminderDateTimeResolver


class ActionExecutor:
    def __init__(
        self,
        projects_client: ProjectsClient,
        workspace_client: WorkspaceClient,
        goals_client: GoalsClient | None = None,
        habits_client: HabitsClient | None = None,
        reminders_client: RemindersClient | None = None,
        github_client: GithubClient | None = None,
    ) -> None:
        self.projects_client = projects_client
        self.workspace_client = workspace_client
        self.goals_client = goals_client
        self.habits_client = habits_client
        self.reminders_client = reminders_client
        self.github_client = github_client

    async def execute(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if decision.action == "none":
            return {
                "executed": False,
                "action": "none",
            }

        if decision.action == "create_project":
            return await self._create_project(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_goal":
            return await self._create_goal(
                user_id=user_id,
                decision=decision,
            )
        
        if decision.action == "create_habit":
            return await self._create_habit(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "create_reminder":
            return await self._create_reminder(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "post_github_comment":
            return await self._post_github_comment(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "approve_github_pr":
            return await self._approve_github_pr(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "merge_github_pr":
            return await self._merge_github_pr(
                user_id=user_id,
                decision=decision,
            )

        if decision.action == "close_github_pr":
            return await self._close_github_pr(
                user_id=user_id,
                decision=decision,
            )

        return {
            "executed": False,
            "action": decision.action,
            "reason": "Action is not implemented yet.",
        }

    async def _create_goal(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if self.goals_client is None:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": "Goals client is not configured.",
            }

        goal_name = decision.goal_name or next(
            (
                signal.name
                for signal in decision.signals
                if signal.type == "goal" and signal.name
            ),
            None,
        )

        if not goal_name:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": "Goal name was not provided.",
            }

        idempotency_key = build_key(user_id, "create_goal", goal_name)

        try:
            existing = await self.goals_client.get_by_name(
                user_id=user_id,
                name=goal_name,
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_goal",
                    "reason": "Goal already exists.",
                    "goal": existing,
                    "goal_created": False,
                    "idempotency_key": idempotency_key,
                }

            goal = await self.goals_client.create_goal(
                user_id=user_id,
                name=goal_name,
                description=decision.goal_description,
                status=decision.goal_status or "active",
                target_date=decision.goal_target_date,
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_goal",
                "reason": f"Goals service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the goal is findable by the same natural key we
        # dedup on before reporting success, rather than trusting the create
        # response alone.
        try:
            verified = await self.goals_client.get_by_name(
                user_id=user_id,
                name=goal_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_goal",
            "goal": verified or goal,
            "goal_created": True,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }

    async def _create_habit(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if self.habits_client is None:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habits client is not configured.",
            }

        if not decision.habit_name:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habit activity was not provided.",
            }

        if not decision.habit_schedule:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": "Habit schedule was not provided.",
            }

        idempotency_key = build_key(user_id, "create_habit", decision.habit_name)

        try:
            existing = await self.habits_client.get_by_name(
                user_id=user_id,
                name=decision.habit_name,
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_habit",
                    "reason": "Habit already exists.",
                    "habit": existing,
                    "habit_created": False,
                    "idempotency_key": idempotency_key,
                }

            habit = await self.habits_client.create_habit(
                user_id=user_id,
                name=decision.habit_name,
                schedule=decision.habit_schedule,
                description=decision.habit_description,
                time_window=decision.habit_time_window,
                status=decision.habit_status or "active",
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_habit",
                "reason": f"Habits service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the habit is findable by the same natural key we
        # dedup on before reporting success, rather than trusting the create
        # response alone.
        try:
            verified = await self.habits_client.get_by_name(
                user_id=user_id,
                name=decision.habit_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_habit",
            "habit": verified or habit,
            "habit_created": True,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }

    @staticmethod
    def _parse_scheduled_for(value: str) -> datetime:
        # Accept an ISO 8601 datetime and normalize to IST. A tz-naive value
        # is assumed to already be IST; an aware value is converted. Raises
        # ValueError on a malformed string (handled by the caller).
        parsed = datetime.fromisoformat(value)
        tz = ZoneInfo("Asia/Kolkata")

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=tz)

        return parsed.astimezone(tz)

    async def _create_reminder(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:

        if self.reminders_client is None:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminders client is not configured.",
            }

        if not decision.reminder_title:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder title was not provided.",
            }

        # Prefer an already-resolved absolute datetime (e.g. from the
        # deterministic Tier-1 cascade). Otherwise fall back to resolving the
        # date + time expressions the LLM decision path emits.
        if decision.reminder_scheduled_for:
            try:
                scheduled_for = self._parse_scheduled_for(
                    decision.reminder_scheduled_for,
                )
            except ValueError:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": "Reminder scheduled_for is not a valid datetime.",
                }

        else:
            if not decision.reminder_date:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": "Reminder date was not provided.",
                }

            if not decision.reminder_time:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": "Reminder time was not provided.",
                }

            try:
                scheduled_for = ReminderDateTimeResolver.resolve(
                    date_expression=decision.reminder_date,
                    time_expression=decision.reminder_time,
                )

            except ValueError as exc:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": str(exc),
                }

        now = datetime.now(
            ZoneInfo("Asia/Kolkata")
        )

        if scheduled_for <= now:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": (
                    "Resolved reminder time is in the past."
                ),
            }

        idempotency_key = build_key(
            user_id,
            "create_reminder",
            decision.reminder_title,
            scheduled_for.isoformat(),
        )

        try:
            existing = await self.reminders_client.get_by_details(
                user_id=user_id,
                title=decision.reminder_title,
                scheduled_for=scheduled_for.isoformat(),
            )

            if existing is not None:
                return {
                    "executed": False,
                    "action": "create_reminder",
                    "reason": "Reminder already exists.",
                    "reminder": existing,
                    "reminder_created": False,
                    "idempotency_key": idempotency_key,
                }

            reminder = await self.reminders_client.create_reminder(
                user_id=user_id,
                title=decision.reminder_title,
                description=decision.reminder_description,
                scheduled_for=scheduled_for.isoformat(),
                recurrence=decision.reminder_recurrence,
                status=decision.reminder_status or "pending",
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": f"Reminders service request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the write is actually queryable before reporting
        # success, rather than trusting the create response alone.
        reminder_id = reminder.get("id") if isinstance(reminder, dict) else None

        if not reminder_id:
            return {
                "executed": False,
                "action": "create_reminder",
                "reason": "Reminder create returned no id; not verified.",
                "reminder": reminder,
                "idempotency_key": idempotency_key,
            }

        try:
            verified = await self.reminders_client.get_reminder(
                user_id=user_id,
                reminder_id=reminder_id,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": True,
            "action": "create_reminder",
            "reminder": verified or reminder,
            "reminder_created": True,
            "verified": verified is not None,
            "scheduled_for": scheduled_for.isoformat(),
            "idempotency_key": idempotency_key,
        }

    async def _post_github_comment(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if self.github_client is None:
            return {
                "executed": False,
                "action": "post_github_comment",
                "reason": "GitHub client is not configured.",
            }

        repo = decision.github_repo
        number = decision.github_number
        body = decision.github_comment_body

        if not repo:
            return {
                "executed": False,
                "action": "post_github_comment",
                "reason": "GitHub repo was not provided.",
            }

        if number is None:
            return {
                "executed": False,
                "action": "post_github_comment",
                "reason": "GitHub PR number was not provided.",
            }

        if not body:
            return {
                "executed": False,
                "action": "post_github_comment",
                "reason": "GitHub comment body was not provided.",
            }

        idempotency_key = build_key(
            user_id,
            "post_github_comment",
            repo,
            str(number),
            body,
        )

        try:
            result = await self.github_client.post_comment(
                user_id=user_id,
                repo=repo,
                number=number,
                body=body,
                idempotency_key=idempotency_key,
            )

        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": "post_github_comment",
                "reason": f"GitHub comment request failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        # The write endpoint returns the created comment, so the response is
        # itself the verification -- no separate read-back GET (a documented
        # deviation from the reminder's read-after-write).
        verified = bool(result.get("id") or result.get("url"))

        return {
            "executed": True,
            "action": "post_github_comment",
            "comment": result,
            "verified": verified,
            "idempotency_key": idempotency_key,
        }

    async def _github_write(
        self,
        *,
        user_id: str,
        action: str,
        repo: str | None,
        number: int | None,
        key_extra: list[str],
        result_field: str,
        verify: Callable[[dict], bool],
        call: Callable[[str], Awaitable[dict]],
        failure_noun: str,
    ) -> dict:
        """Shared spine for the approve/merge/close PR writes.

        Guards the client + required slots (each with its own honest
        ``executed:False`` reason), derives the per-action idempotency key
        (``key_extra`` distinguishes e.g. one merge method from another), then
        runs ``call`` and grades the write off its own response via ``verify``
        -- no read-back GET, exactly as the comment write documents. A GitHub
        (or downstream) HTTP error is a graceful soft-fail, never a raise.
        """

        if self.github_client is None:
            return {
                "executed": False,
                "action": action,
                "reason": "GitHub client is not configured.",
            }

        if not repo:
            return {
                "executed": False,
                "action": action,
                "reason": "GitHub repo was not provided.",
            }

        if number is None:
            return {
                "executed": False,
                "action": action,
                "reason": "GitHub PR number was not provided.",
            }

        idempotency_key = build_key(user_id, action, repo, str(number), *key_extra)

        try:
            result = await call(idempotency_key)
        except httpx.HTTPError as exc:
            return {
                "executed": False,
                "action": action,
                "reason": f"{failure_noun} failed: {exc}",
                "idempotency_key": idempotency_key,
            }

        return {
            "executed": True,
            "action": action,
            result_field: result,
            "verified": verify(result),
            "idempotency_key": idempotency_key,
        }

    async def _approve_github_pr(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        repo = decision.github_repo
        number = decision.github_number
        body = decision.github_comment_body

        async def call(key: str) -> dict:
            return await self.github_client.approve_pr(
                user_id=user_id,
                repo=repo,
                number=number,
                body=body,
                idempotency_key=key,
            )

        return await self._github_write(
            user_id=user_id,
            action="approve_github_pr",
            repo=repo,
            number=number,
            key_extra=[body] if body else [],
            result_field="review",
            verify=lambda r: bool(r.get("id") or r.get("state") == "APPROVED"),
            call=call,
            failure_noun="GitHub approve request",
        )

    async def _merge_github_pr(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        repo = decision.github_repo
        number = decision.github_number
        merge_method = decision.github_merge_method or "merge"

        async def call(key: str) -> dict:
            return await self.github_client.merge_pr(
                user_id=user_id,
                repo=repo,
                number=number,
                merge_method=merge_method,
                idempotency_key=key,
            )

        return await self._github_write(
            user_id=user_id,
            action="merge_github_pr",
            repo=repo,
            number=number,
            key_extra=[merge_method],
            result_field="merge",
            verify=lambda r: bool(r.get("merged")),
            call=call,
            failure_noun="GitHub merge request",
        )

    async def _close_github_pr(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        repo = decision.github_repo
        number = decision.github_number

        async def call(key: str) -> dict:
            return await self.github_client.close_pr(
                user_id=user_id,
                repo=repo,
                number=number,
                idempotency_key=key,
            )

        return await self._github_write(
            user_id=user_id,
            action="close_github_pr",
            repo=repo,
            number=number,
            key_extra=[],
            result_field="closure",
            verify=lambda r: r.get("state") == "closed",
            call=call,
            failure_noun="GitHub close request",
        )

    async def _create_project(
        self,
        user_id: str,
        decision: ContextDecision,
    ) -> dict:
        if not decision.project_name:
            return {
                "executed": False,
                "action": "create_project",
                "reason": "Project name was not provided.",
            }

        idempotency_key = build_key(
            user_id,
            "create_project",
            decision.project_name,
        )

        project = None
        space = None
        association = None
        project_created = False
        space_created = False

        try:
            # --------------------------------------------------
            # Project
            # --------------------------------------------------

            project = await self.projects_client.get_by_name(
                user_id=user_id,
                name=decision.project_name,
            )

            if project is None:
                project = await self.projects_client.create_project(
                    user_id=user_id,
                    name=decision.project_name,
                    description=decision.project_description,
                    idempotency_key=idempotency_key,
                )
                project_created = True

            # --------------------------------------------------
            # Space
            # --------------------------------------------------

            if decision.space_candidate:
                space = await self.workspace_client.get_by_name(
                    user_id=user_id,
                    name=decision.space_candidate,
                )

                if space is None:
                    space = await self.workspace_client.create_space(
                        user_id=user_id,
                        name=decision.space_candidate,
                        description=decision.project_description,
                        space_type="custom",
                        visibility="private",
                        source="ai",
                    )
                    space_created = True

            # --------------------------------------------------
            # Association
            # --------------------------------------------------

            if space is not None:
                association = await self.workspace_client.associate_project(
                    space_id=space["id"],
                    project_id=project["id"],
                )

        except httpx.HTTPError as exc:
            return {
                "executed": project_created or space_created,
                "action": "create_project",
                "reason": f"Projects service request failed: {exc}",
                "project": project,
                "space": space,
                "project_created": project_created,
                "space_created": space_created,
                "idempotency_key": idempotency_key,
            }

        # Read-back: confirm the project is findable by name before reporting
        # success, rather than trusting the create response alone.
        try:
            verified = await self.projects_client.get_by_name(
                user_id=user_id,
                name=decision.project_name,
            )
        except httpx.HTTPError:
            verified = None

        return {
            "executed": project_created or space_created,
            "action": "create_project",
            "project": verified or project,
            "space": space,
            "association": association,
            "project_created": project_created,
            "space_created": space_created,
            "verified": verified is not None,
            "idempotency_key": idempotency_key,
        }
