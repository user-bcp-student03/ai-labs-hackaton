import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEFAULT_DATABASE_PATH, DEFAULT_UPLOAD_DIRECTORY
from app.repositories.tasks import initialize_tasks
from app.routes.backend_health import router as backend_health_router
from app.routes.summary import router as summary_router
from app.routes.tasks import router as tasks_router
from app.routes.uploads import router as uploads_router


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", DEFAULT_DATABASE_PATH)
    selected_uploads = upload_dir or os.getenv(
        "WORKSHOP_UPLOAD_DIR",
        DEFAULT_UPLOAD_DIRECTORY,
    )
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    initialize_tasks(connection)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            connection.close()

    app = FastAPI(
        title="Workshop Requirements API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(tasks_router)
    app.include_router(summary_router)
    app.include_router(uploads_router)
    app.include_router(backend_health_router)
    return app


app = create_app()
