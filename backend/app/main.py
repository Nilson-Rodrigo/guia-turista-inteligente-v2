from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers.auth import router as auth_router
from .routers.roteiros import router as roteiros_router
from .routers.telemetria import router as telemetria_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(6.0))
    app.state.ready = True
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        app.state.ready = False


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API assíncrona para planejamento de viagens no Brasil.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(roteiros_router)
app.include_router(auth_router)
app.include_router(telemetria_router)


@app.middleware("http")
async def observabilidade(request, call_next):
    inicio = perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(perf_counter() - inicio) * 1000:.2f}ms"
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", uuid4().hex)
    return response


@app.get("/healthz", tags=["Operação"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["Operação"])
async def readyz() -> dict[str, str]:
    status = "ready" if getattr(app.state, "ready", False) else "starting"
    return {"status": status}


@app.get("/metrics", include_in_schema=False)
async def metrics_root():
    from .routers.telemetria import metrics

    return await metrics()
