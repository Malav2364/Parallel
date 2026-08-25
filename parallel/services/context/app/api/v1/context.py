from fastapi import APIRouter, Depends, Header
import copy
from app.api.deps import (
    get_action_executor,
    get_context_decision_engine,
    get_context_extractor,
    get_context_service,
    get_project_activity_extractor,
    get_project_resolver,
    get_projects_client,
    get_semantic_project_resolver,
    get_understanding_engine,
)
from app.clients.projects_client import ProjectsClient
from app.nlu.compose import with_message
from app.nlu.confirmation import clarification_prompt, confirmation_prompt
from app.nlu.mapping import to_decision
from app.nlu.rules import merge_answer, propose
from app.nlu.schemas import ProposedAction
from app.schemas import (
    ContextAnalyzeRequest,
    ContextDecision,
    ContextExtractRequest,
    ContextProcessRequest,
    ContextResponse,
    ContextUpdate,
    ProjectResolution,
)
from app.services import (
    ActionExecutor,
    ContextDecisionEngine,
    ContextExtraction,
    ContextExtractor,
    ContextService,
    ProjectResolver,
    UnderstandingEngine,
)
from app.services.project_activity_extractor import (
    ProjectActivityExtractor,
)
from app.services.semantic_project_resolver import SemanticProjectResolver

router = APIRouter()


def _to_response(context) -> ContextResponse:
    return ContextResponse(
        user_id=context.user_id,
        context=context.context,
        version=context.version,
    )


def _find_project_by_id(
    projects: list[dict],
    project_id: str | None,
) -> dict | None:
    if not project_id:
        return None

    return next(
        (project for project in projects if project["id"] == project_id),
        None,
    )


@router.get("", response_model=ContextResponse)
def get_context(
    x_user_id: str = Header(...),
    service: ContextService = Depends(get_context_service),
) -> ContextResponse:
    return _to_response(service.get_context(x_user_id))


@router.patch("", response_model=ContextResponse)
def update_context(
    request: ContextUpdate,
    x_user_id: str = Header(...),
    service: ContextService = Depends(get_context_service),
) -> ContextResponse:
    return _to_response(service.update_context(x_user_id, request))


@router.get("/changes")
def get_context_changes(
    x_user_id: str = Header(...),
    service: ContextService = Depends(get_context_service),
):
    return service.list_changes(x_user_id)


@router.post("/extract", response_model=ContextExtraction)
def extract_context(
    request: ContextExtractRequest,
    x_user_id: str = Header(...),
    service: ContextService = Depends(get_context_service),
    extractor: ContextExtractor = Depends(get_context_extractor),
) -> ContextExtraction:
    context = service.get_context(x_user_id)
    return extractor.extract(request.message, context.context)


@router.post("/analyze", response_model=ContextDecision)
def analyze_context(
    request: ContextAnalyzeRequest,
    x_user_id: str = Header(...),
    service: ContextService = Depends(get_context_service),
    extractor: ContextExtractor = Depends(get_context_extractor),
    decision_engine: ContextDecisionEngine = Depends(
        get_context_decision_engine,
    ),
) -> ContextDecision:
    context = service.get_context(x_user_id)
    extraction = extractor.extract(
        user_input=request.message,
        current_context=context.context,
    )
    return decision_engine.evaluate(
        user_input=request.message,
        current_context=context.context,
        extraction=extraction,
    )


@router.post("/resolve-project", response_model=ProjectResolution)
async def resolve_project(
    request: ContextAnalyzeRequest,
    x_user_id: str = Header(...),
    resolver: ProjectResolver = Depends(get_project_resolver),
) -> ProjectResolution:
    return await resolver.resolve(
        user_id=x_user_id,
        user_input=request.message,
    )


@router.post("/process")
async def process_context(
    request: ContextProcessRequest,
    x_user_id: str = Header(...),
    context_service: ContextService = Depends(
        get_context_service,
    ),
    extractor: ContextExtractor = Depends(
        get_context_extractor,
    ),
    understanding: UnderstandingEngine = Depends(
        get_understanding_engine,
    ),
    executor: ActionExecutor = Depends(
        get_action_executor,
    ),
    resolver: ProjectResolver = Depends(
        get_project_resolver,
    ),
    projects_client: ProjectsClient = Depends(
        get_projects_client,
    ),
    semantic_resolver: SemanticProjectResolver = Depends(
        get_semantic_project_resolver,
    ),
):
    if request.pending_action is not None:
        # Answering a prior needs_confirmation: fill the missing slot from the
        # reply and execute deterministically. This is a terse slot answer, not
        # a fresh utterance, so the LLM context extractor is intentionally
        # skipped -- the whole confirmation loop stays model-free.
        merged = merge_answer(
            ProposedAction.model_validate(request.pending_action),
            request.message,
        )

        if merged.is_executable:
            decision = to_decision(merged)
            execution = await executor.execute(
                user_id=x_user_id,
                decision=decision,
            )
            return with_message(
                {
                    "type": (
                        "new_intent" if execution.get("executed") else "context_only"
                    ),
                    "extraction": None,
                    "context_update": None,
                    "resolution": None,
                    "resolution_error": None,
                    "activity": None,
                    "activity_project": None,
                    "decision": decision,
                    "execution": execution,
                    "tier": "rules",
                    "pending_action": None,
                    "prompt": None,
                }
            )

        # Still incomplete. A MEDIUM proposal needs one more slot (ask for it);
        # a LOW one is still category-ambiguous (ask the user to pick again).
        if merged.band == "medium":
            return with_message(
                {
                    "type": "needs_confirmation",
                    "extraction": None,
                    "context_update": None,
                    "resolution": None,
                    "resolution_error": None,
                    "activity": None,
                    "activity_project": None,
                    "decision": None,
                    "execution": None,
                    "tier": "rules",
                    "pending_action": merged,
                    "prompt": confirmation_prompt(merged),
                }
            )

        return with_message(
            {
                "type": "needs_clarification",
                "extraction": None,
                "context_update": None,
                "resolution": None,
                "resolution_error": None,
                "activity": None,
                "activity_project": None,
                "decision": None,
                "execution": None,
                "tier": "rules",
                "pending_action": merged,
                "prompt": clarification_prompt(merged),
            }
        )

    context = context_service.get_context(
        x_user_id,
    )

    original_context = copy.deepcopy(context.context)

    extraction = extractor.extract(
        user_input=request.message,
        current_context=original_context,
    )

    context_update = context_service.apply_updates(
        user_id=x_user_id,
        updates=extraction.updates,
    )

    proposal = propose(request.message)

    if proposal is not None and proposal.is_executable:
        # Deterministic Tier-1 hit: build the decision directly and skip the
        # project resolver, activity extractor, and decision-engine LLM calls.
        # The context extractor above still ran, so a co-occurring context
        # update is not lost.
        decision = to_decision(proposal)
        resolution = None
        resolution_error = None
        activity = None
        activity_project = None
        tier = "rules"
        resolution_source = None

    elif proposal is not None and proposal.band == "medium":
        # Tier-1 recognised the intent but a required slot is missing. Ask for
        # it (never silently wrong) instead of guessing or falling to the LLM.
        # The context extractor above still ran, so a co-occurring context
        # update is not lost. The prefilled slots ride back on pending_action
        # so the client can echo them with the user's answer next turn.
        return with_message(
            {
                "type": "needs_confirmation",
                "extraction": extraction,
                "context_update": context_update.context,
                "resolution": None,
                "resolution_error": None,
                "activity": None,
                "activity_project": None,
                "decision": None,
                "execution": None,
                "tier": "rules",
                "pending_action": proposal,
                "prompt": confirmation_prompt(proposal),
            }
        )

    elif proposal is not None:
        # Tier-1 sees an actionable intent but can't tell which category it is
        # (a recurring activity that could be a habit or a recurring reminder).
        # Ask the user to pick rather than escalating to the LLM to guess. The
        # candidates ride back on pending_action for the answer turn.
        return with_message(
            {
                "type": "needs_clarification",
                "extraction": extraction,
                "context_update": context_update.context,
                "resolution": None,
                "resolution_error": None,
                "activity": None,
                "activity_project": None,
                "decision": None,
                "execution": None,
                "tier": "rules",
                "pending_action": proposal,
                "prompt": clarification_prompt(proposal),
            }
        )

    else:
        # Tier-2 (local semantic NLU). Fetch the user's projects once, then try
        # to resolve which one the message is about via in-process cosine over
        # cached embeddings. A confident, unambiguous match skips the slower,
        # non-deterministic Gemini resolver; anything uncertain (or no projects
        # at all) falls through to it rather than guessing.
        projects = await projects_client.list_projects(
            x_user_id,
        )

        activity = None
        activity_project = None
        resolution_error = None

        if projects:
            resolution = await semantic_resolver.resolve(
                user_id=x_user_id,
                user_input=request.message,
                projects=projects,
            )
            resolution_source = "nlu" if resolution.matched else "llm"

            if not resolution.matched:
                # Semantic miss: reuse the projects already fetched above so the
                # Gemini resolver doesn't re-fetch them itself.
                resolution = await resolver.resolve(
                    user_id=x_user_id,
                    user_input=request.message,
                    projects=projects,
                )
        else:
            resolution = ProjectResolution(
                matched=False,
                confidence=1.0,
                reason="The user has no existing projects.",
            )
            resolution_source = "nlu"

        project = None
        if resolution.matched:
            project = _find_project_by_id(
                projects=projects,
                project_id=resolution.project_id,
            )

            if project is None:
                resolution_error = "Resolved project could not be found."

        # One Gemini call replaces the former activity-extractor + decision-
        # engine pair: it decides and, when a project resolved cleanly, reports
        # that project's current_focus / latest_activity in the same structured
        # response. Activity and the decision are independent, so merging them
        # drops a Tier-2-hit turn from two model calls to one.
        result = understanding.decide(
            user_input=request.message,
            current_context=context.context,
            extraction=extraction,
            project_resolution=resolution,
            project=project if resolution_error is None else None,
        )

        decision = result.decision
        activity = result.activity

        if (
            project is not None
            and activity is not None
            and (
                activity.current_focus is not None
                or activity.latest_activity is not None
            )
        ):
            activity_project = await projects_client.update_activity(
                project_id=resolution.project_id,
                current_focus=activity.current_focus,
                latest_activity=activity.latest_activity,
            )

        tier = "llm"

    execution = await executor.execute(
        user_id=x_user_id,
        decision=decision,
    )

    matched = bool(resolution and resolution.matched)

    if matched and execution.get("executed"):
        response_type = "multi_intent"
    elif matched:
        response_type = "existing_project"
    elif execution.get("executed"):
        response_type = "new_intent"
    else:
        response_type = "context_only"

    return with_message(
        {
            "type": response_type,
            "extraction": extraction,
            "context_update": context_update.context,
            "resolution": resolution,
            "resolution_error": resolution_error,
            "activity": activity,
            "activity_project": activity_project,
            "decision": decision,
            "execution": execution,
            "tier": tier,
            "resolution_source": resolution_source,
            "pending_action": None,
            "prompt": None,
        }
    )


@router.post(
    "/project-activity",
)
async def extract_project_activity(
    request: ContextAnalyzeRequest,
    x_user_id: str = Header(...),
    resolver: ProjectResolver = Depends(
        get_project_resolver,
    ),
    extractor: ProjectActivityExtractor = Depends(get_project_activity_extractor),
):
    resolution = await resolver.resolve(
        user_id=x_user_id,
        user_input=request.message,
    )

    if not resolution.matched:
        return {
            "matched": False,
            "activity": None,
        }

    projects = await resolver.projects_client.list_projects(
        x_user_id,
    )

    project = next(
        (project for project in projects if project["id"] == resolution.project_id),
        None,
    )

    if project is None:
        return {
            "matched": False,
            "activity": None,
        }

    activity = extractor.extract(
        user_input=request.message,
        project=project,
    )

    return {
        "matched": True,
        "project_id": resolution.project_id,
        "activity": activity,
    }
