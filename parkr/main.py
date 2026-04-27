from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from parkr.database import create_tables
from parkr.routes import spots_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_tables()
        print("Startup: Database ready")
    except Exception as e:
        print(f"Startup error: {e}")
        raise
    yield
    print("Shutdown: App stopped")


app = FastAPI(
    title="Parkr API",
    description=(
        "Real-time crowdsourced parking — MVP backend.\n\n"
        "Private spots: reservations + guaranteed availability.\n"
        "Street spots: discovery only, no reservations."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(spots_router, prefix="/api/v1", tags=["spots"])


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}