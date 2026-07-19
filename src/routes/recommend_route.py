from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from src.loader.database import get_connection
from src.recommender.postgres_store import PostgresEmbeddingStore 
from src.recommender.recommend import Recommender
from src.services.fic_resolver import FicResolver
from src.services.ingestion_service import IngestionService
from src.services.normalize import normalize_row
from src.services.format_author import format_author
from . import templates as loc


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