from fastapi import FastAPI
from app.presentation.middleware import setup_logging, AccessLogMiddleware, metrics_endpoint
from app.presentation.routes_auth import router as auth_router
from app.presentation.routes_users import router as users_router
from app.presentation.routes_payments import router as payments_router
from app.presentation.routes_generations import router as generations_router

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="gen-svc")
    app.add_middleware(AccessLogMiddleware)

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(payments_router)
    app.include_router(generations_router)

    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
    return app
