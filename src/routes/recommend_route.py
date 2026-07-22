from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from src.loader.database import get_connection
from src.recommender.postgres_store import PostgresEmbeddingStore
from src.recommender.recommend import Recommender
from src.services.fic_resolver import FicResolver
from src.services.format_author import format_author
from src.services.ingestion_service import IngestionService
from src.services.normalize import normalize_row

from . import templates as loc


router = APIRouter()

templates = Jinja2Templates(directory=loc)


@router.get("/recommend")
async def recommend_page(request: Request):
    """Render the main recommendation page HTML template."""
    return templates.TemplateResponse(request=request, name="recommend.html")


@router.post("/recommend")
async def recommend_api(request: Request):
    """API endpoint for fetching recommendations, ingesting works on demand if missing."""
    payload = await request.json()

    # Stage 1: Attempt local database resolution first
    resolver = FicResolver(payload)
    source = resolver.resolve()

    # Stage 2: Not in database -> ingest fanfiction work
    if "error" in source:
        ingestion_service = IngestionService(payload)
        ingestion_result = ingestion_service.ingest()

        if "error" in ingestion_result:
            return JSONResponse(ingestion_result, status_code=400)

        # Ingestion inserts the fic into DB; re-resolve record
        source = FicResolver(payload).resolve()

        if "error" in source:
            return JSONResponse(
                {"error": "The fic was ingested but could not be retrieved afterwards."},
                status_code=500,
            )

        source["newly_indexed"] = True
    else:
        source["newly_indexed"] = False

    # Stage 3: Generate hybrid recommendations using embedding store
    embedding_store = PostgresEmbeddingStore()

    with get_connection() as connection:
        recommender = Recommender(
            embedding_store=embedding_store,
            connection=connection,
        )

        try:
            recommendation_tuples = recommender.recommend(fic_id=source["fic_id"])
        except KeyError:
            return JSONResponse(
                {
                    "error": (
                        "This fic exists in Opsis, but its recommendation data "
                        "is incomplete. Please try again later."
                    )
                },
                status_code=500,
            )

    # Stage 4: Convert candidate IDs into full objects with rounded scores
    recommendations = []

    for fic_id, score in recommendation_tuples:
        recommendation = FicResolver({"fic_id": fic_id}).resolve_from_id()

        if "error" in recommendation:
            continue

        recommendation["score"] = round(score * 100, 1)
        recommendations.append(recommendation)

    # Stage 5: Normalize and format author and chapter metadata
    source["author"] = format_author(source.get("author"))
    source["chapters"] = (
        source["current_chapters"]
        if not source["total_chapters"]
        else source["total_chapters"]
    )

    for recommendation in recommendations:
        recommendation["author"] = format_author(recommendation.get("author"))
        recommendation["chapters"] = (
            recommendation["current_chapters"]
            if not recommendation["total_chapters"]
            else recommendation["total_chapters"]
        )

    # Stage 6: Return normalized JSON response payload
    return JSONResponse(
        normalize_row({
            "source": source,
            "recommendations": recommendations,
        })
    )