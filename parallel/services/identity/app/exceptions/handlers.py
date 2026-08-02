from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.exceptions.exceptions import ParallelException
from app.schemas.error import ErrorDetail, ErrorResponse


async def parallel_exception_handler(
    request: Request,
    exc: ParallelException,
):
    response = ErrorResponse(
        error=ErrorDetail(
            code=exc.error_code,
            message=exc.message,
        ),
        timestamp=datetime.now(UTC).isoformat(),
        path=request.url.path,
    )
    logger.error(
        "%s: %s | Path: %s",
        exc.error_code,
        exc.message,
        request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )
