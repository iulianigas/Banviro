from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.tracing import setup_phoenix_tracing
from app.api.router import api_router
from app.config import settings
from app.logging_config import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_phoenix_tracing()
    yield


app = FastAPI(
    title="Banviro API",
    description="Personal finance tracker backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Banviro API", "docs": "/docs"}
