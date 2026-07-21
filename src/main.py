print("Starting FastAPI application...")
from fastapi import FastAPI
print("FastAPI application started successfully.")
from fastapi.staticfiles import StaticFiles
print("StaticFiles module imported successfully.")

from src.routes.index_route import router as index_router
print("Index route imported successfully.")
from src.routes.about_route import router as about_router
print("About route imported successfully.")
from src.routes.recommend_route import router as recommend_router
print("Recommend route imported successfully.")
from . import static as loc
print("Static files location imported successfully.")

app = FastAPI()
print("FastAPI application instance created successfully.")

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