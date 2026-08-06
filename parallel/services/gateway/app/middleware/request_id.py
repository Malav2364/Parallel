import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        request.state.request_id = str(uuid.uuid4())

        start = time.perf_counter()

        response = await call_next(request)

        elapsed = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Response-Time"] = f"{elapsed:.2f} ms"

        return response
