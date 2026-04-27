from contextlib import asynccontextmanager

from fastapi import FastAPI

from parkr.database import create_tables
from parkr.routes import spots_router
from scripts.seed_demo_data import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # SYNC call (NO await)
        create_tables()
        seed_demo_data()
        print("Startup: Database ready and seeded")
    except Exception as e:
        print(f"Startup error: {e}")
        raise
    yield
    print("Shutdown: App stopped")


from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spots_router, prefix="/api/v1", tags=["spots"])


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}