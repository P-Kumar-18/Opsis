from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routes.about_route import router as about_router
from src.routes.index_route import router as index_router
from src.routes.recommend_route import router as recommend_router

from . import static as loc


app = FastAPI(
    title="Opsis Fanfiction Recommender",
    description="A content-based and hybrid recommendation service for AO3 works.",
    version="1.0.0",
)

# Mount static file directory for web assets
app.mount("/static", StaticFiles(directory=loc), name="static")

# Register application routes
app.include_router(index_router)
app.include_router(about_router)
app.include_router(recommend_router)