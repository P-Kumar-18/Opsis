print("Starting main.py", flush=True)
from fastapi import FastAPI
print("Imported FastAPI", flush=True)
from fastapi.staticfiles import StaticFiles
print("Imported index router", flush=True)

from src.routes.index_route import router as index_router
print("Index route imported successfully.", flush=True)
from src.routes.about_route import router as about_router
print("About route imported successfully.", flush=True)
from src.routes.recommend_route import router as recommend_router
print("Recommend route imported successfully.", flush=True)
from . import static as loc
print("Static files location imported successfully.", flush=True)

app = FastAPI()
print("FastAPI application instance created successfully.", flush=True)

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