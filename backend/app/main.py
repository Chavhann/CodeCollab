from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.auth_routes import router as auth_router
from app.collaboration_routes import router as collaboration_router
from app.database import Base, engine
from app.file_routes import router as file_router
from app.persistence_queue import persistence_queue
from app.version_routes import router as version_router
from app.workspace_routes import router as workspace_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await persistence_queue.start()

    try:
        yield
    finally:
        await persistence_queue.stop()


app = FastAPI(
    title="CodeCollab API",
    version="0.7.0",
    description="Real-time collaborative development platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(file_router)
app.include_router(version_router)
app.include_router(collaboration_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "codecollab-api",
    }
