from fastapi import APIRouter, Depends, Header

from app.api.deps import (
    get_action_executor,
    get_context_decision_engine,
    get_context_extractor,
    get_context_service,
    get_project_activity_extractor,
    get_project_resolver,
    get_projects_client,
)
from app.schemas import (
    ContextAnalyzeRequest,
    ContextDecision,
    ContextExtractRequest,
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
)
from app.services.project_activity_extractor import (
    ProjectActivityExtractor,
)
from app.clients.projects_client import ProjectsClient

router = APIRouter()


def _to_response(context) -> ContextResponse:
    return ContextResponse(
        user_id=context.user_id,
        context=context.context,
        version=context.version,
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
def resolve_project(
    request: ContextAnalyzeRequest,
    x_user_id: str = Header(...),
    resolver: ProjectResolver = Depends(get_project_resolver),
) -> ProjectResolution:
    return resolver.resolve(
        user_id=x_user_id,
        user_input=request.message,
    )


@router.post("/process")
def process_context(
    request: ContextAnalyzeRequest,
    x_user_id: str = Header(...),
    context_service: ContextService = Depends(
        get_context_service,
    ),
    extractor: ContextExtractor = Depends(
        get_context_extractor,
    ),
    decision_engine: ContextDecisionEngine = Depends(
        get_context_decision_engine,
    ),
    executor: ActionExecutor = Depends(
        get_action_executor,
    ),
    resolver: ProjectResolver = Depends(
        get_project_resolver,
    ),
    activity_extractor: ProjectActivityExtractor = Depends(
        get_project_activity_extractor,
    ),
    projects_client: ProjectsClient = Depends(
        get_projects_client,
    ),
):
    # ---------------------------------------------------------
    # 1. Load current user context
    # ---------------------------------------------------------

    context = context_service.get_context(
        x_user_id,
    )

    # ---------------------------------------------------------
    # 2. Try to resolve the message to an existing project
    # ---------------------------------------------------------

    resolution = resolver.resolve(
        user_id=x_user_id,
        user_input=request.message,
    )

    # ---------------------------------------------------------
    # 3. Existing project found
    # ---------------------------------------------------------

    if resolution.matched:
        projects = projects_client.list_projects(
            x_user_id,
        )

        project = next(
            (
                project
                for project in projects
                if project["id"] == resolution.project_id
            ),
            None,
        )

        if project is None:
            return {
                "type": "project_resolution_error",
                "resolution": resolution,
                "message": "Resolved project could not be found.",
            }

        # Extract what changed inside the project
        activity = activity_extractor.extract(
            user_input=request.message,
            project=project,
        )

        updated_project = None

        # Only update the project when useful activity exists
        if (
            activity.current_focus is not None
            or activity.latest_activity is not None
        ):
            updated_project = projects_client.update_activity(
                project_id=resolution.project_id,
                current_focus=activity.current_focus,
                latest_activity=activity.latest_activity,
            )

        return {
            "type": "existing_project",
            "resolution": resolution,
            "activity": activity,
            "project": updated_project,
        }

    # ---------------------------------------------------------
    # 4. No existing project found
    # ---------------------------------------------------------

    extraction = extractor.extract(
        user_input=request.message,
        current_context=context.context,
    )

    context_update = context_service.apply_updates(
        user_id=x_user_id,
        updates=extraction.updates,
    )

    # ---------------------------------------------------------
    # 5. Decide what PIOS should do
    # ---------------------------------------------------------

    decision = decision_engine.evaluate(
        user_input=request.message,
        current_context=context.context,
        extraction=extraction,
    )

    # ---------------------------------------------------------
    # 6. Execute the decision
    # ---------------------------------------------------------

    execution = executor.execute(
        user_id=x_user_id,
        decision=decision,
    )

    # ---------------------------------------------------------
    # 7. Return complete result
    # ---------------------------------------------------------

    return {
        "type": "new_intent",
        "extraction": extraction,
        "context_update": context_update.context,
        "decision": decision,
        "execution": execution,
    }

@router.post(
    "/project-activity",
)
def extract_project_activity(
        request: ContextAnalyzeRequest,
        x_user_id: str = Header(...),
        resolver: ProjectResolver = Depends(
            get_project_resolver,
        ),
        extractor: ProjectActivityExtractor = Depends(
            get_project_activity_extractor
        ),
    ):
        resolution = resolver.resolve(
            user_id=x_user_id,
            user_input=request.message,
        )

        if not resolution.matched:
            return {
                "matched": False,
                "activity": None,
            }

        projects = resolver.projects_client.list_projects(
            x_user_id,
        )

        project = next(
            (
                project
                for project in projects
                if project["id"] == resolution.project_id
            ),
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
