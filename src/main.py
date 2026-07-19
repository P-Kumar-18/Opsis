from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routes.index_route import router as index_router
from src.routes.about_route import router as about_router
from src.routes.recommend_route import router as recommend_router
from . import static as loc

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(
        directory = loc
    ),
    name = "static",
)

app.include_router(
    index_router
)

app.include_router(
    about_router
)

app.include_router(
    recommend_router
)