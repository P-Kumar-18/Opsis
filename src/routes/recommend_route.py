print("Starting recommend_route", flush=True)

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

print("FastAPI imports done", flush=True)

from src.loader.database import get_connection
print("database imported", flush=True)

from src.recommender.postgres_store import PostgresEmbeddingStore
print("postgres_store imported", flush=True)

from src.recommender.recommend import Recommender
print("recommender imported", flush=True)

from src.services.fic_resolver import FicResolver
print("fic_resolver imported", flush=True)

from src.services.ingestion_service import IngestionService
print("ingestion_service imported", flush=True)

from src.services.normalize import normalize_row
print("normalize imported", flush=True)

from src.services.format_author import format_author
print("format_author imported", flush=True)

from . import templates as loc

print("recommend_route imports complete", flush=True)


router = APIRouter()

templates = Jinja2Templates(
    directory = loc
)


@router.get("/recommend")
async def recommend_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="recommend.html",
    )

@router.post("/recommend")
async def recommend_api(
    request: Request,
):

    payload = await request.json()

    # ---------------------------------
    # Attempt local resolution first
    # ---------------------------------

    resolver = FicResolver(
        payload
    )

    source = resolver.resolve()

    # ---------------------------------
    # Not in database -> ingest
    # ---------------------------------

    if "error" in source:
        print("Fic not found in database. Attempting ingestion...", source)
        ingestion_service = (
            IngestionService(
                payload
            )
        )
        print("Ingesting fic...", payload)

        ingestion_result = (
            ingestion_service.ingest()
        )
        print("Ingestion result:", ingestion_result)

        if "error" in ingestion_result:
            return JSONResponse(
                ingestion_result,
                status_code=400,
            )

        # Ingestion should have inserted
        # the fic into the DB already.
        source = (
            FicResolver(
                payload
            ).resolve()
        )

        if "error" in source:
            return JSONResponse(
                {
                    "error":
                    (
                        "The fic was ingested "
                        "but could not be "
                        "retrieved afterwards."
                    )
                },
                status_code=500,
            )

        source[
            "newly_indexed"
        ] = True

    else:
        source[
            "newly_indexed"
        ] = False

    # ---------------------------------
    # Generate recommendations
    # ---------------------------------

    embedding_store = (
        PostgresEmbeddingStore()
    )

    with get_connection() as connection:

        recommender = Recommender(
            embedding_store=
                embedding_store,

            connection=
                connection,
        )

        try:
            recommendation_tuples = (
                recommender.recommend(
                    fic_id=
                        source["fic_id"]
                )
            )

        except KeyError:
            return JSONResponse(
                {
                    "error": (
                        "This fic exists in Opsis, "
                        "but its recommendation data "
                        "is incomplete. Please try "
                        "again later."
                    )
                },
                status_code=500,
            )

    # ---------------------------------
    # Convert tuples into full objects
    # ---------------------------------

    recommendations = []

    for fic_id, score in recommendation_tuples:

        recommendation = (
            FicResolver(
                {
                    "fic_id":
                        fic_id
                }
            ).resolve_from_id()
        )

        if "error" in recommendation:
            continue

        recommendation[
            "score"
        ] = round(
            score * 100,
            1
        )

        recommendations.append(
            recommendation
        )
    
    # ---------------------------------
    # Normalizing
    # ---------------------------------
    
    source["author"] = format_author(
        source.get("author")
    )
    source["chapters"] = source["current_chapters"] if not source["total_chapters"] else source["total_chapters"]

    for recommendation in recommendations:
        recommendation["author"] = format_author(
            recommendation.get("author")
        )
        recommendation["chapters"] = recommendation["current_chapters"] if not recommendation["total_chapters"] else recommendation["total_chapters"]
    # ---------------------------------
    # Final response
    # ---------------------------------

    return JSONResponse(normalize_row({
       "source": source,
       "recommendations": recommendations,
   }))