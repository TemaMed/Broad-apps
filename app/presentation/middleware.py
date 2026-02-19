import os, logging
from logging.handlers import TimedRotatingFileHandler
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.infrastructure.metrics import api_requests_total
from app.settings import settings

def setup_logging() -> None:
    os.makedirs(settings.log_dir, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)

    fh = TimedRotatingFileHandler(
        filename=os.path.join(settings.log_dir, "app.log"),
        when="D",
        interval=1,
        backupCount=7,
        utc=True,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        api_requests_total.labels(path=request.url.path, method=request.method, status=str(resp.status_code)).inc()
        logging.getLogger("access").info(
            f'{request.client.host} {request.method} {request.url.path} {resp.status_code}'
        )
        return resp

async def metrics_endpoint(_: Request) -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
