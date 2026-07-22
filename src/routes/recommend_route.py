from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from time import perf_counter

from src.loader.database import get_connection
from src.recommender.postgres_store import PostgresEmbeddingStore
from src.recommender.recommend import Recommender
from src.services.fic_resolver import FicResolver
from src.services.format_author import format_author
from src.services.ingestion_service import IngestionService
from src.services.normalize import normalize_row
from src.services.explanation_service import ExplanationService

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
    total_start = perf_counter()

    payload = await request.json()

    # Stage 1: Attempt local database resolution first
    stage_start = perf_counter()

    resolver = FicResolver(payload)
    source = resolver.resolve()

    print(
        f"TIMING | Source resolution: {perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    # Stage 2: Not in database -> ingest fanfiction work
    if "error" in source:
        stage_start = perf_counter()

        ingestion_service = IngestionService(payload)
        ingestion_result = ingestion_service.ingest()

        print(
            f"TIMING | Ingestion: {perf_counter() - stage_start:.2f}s",
            flush=True,
        )

        if "error" in ingestion_result:
            return JSONResponse(ingestion_result, status_code=400)

        # Ingestion inserts the fic into DB; re-resolve record
        stage_start = perf_counter()

        source = FicResolver(payload).resolve()

        print(
            f"TIMING | Post-ingestion resolution: "
            f"{perf_counter() - stage_start:.2f}s",
            flush=True,
        )

        if "error" in source:
            return JSONResponse(
                {"error": "The fic was ingested but could not be retrieved afterwards."},
                status_code=500,
            )

        source["newly_indexed"] = True
    else:
        source["newly_indexed"] = False

    # Stage 3: Generate hybrid recommendations using embedding store
    stage_start = perf_counter()

    embedding_store = PostgresEmbeddingStore()

    with get_connection() as connection:
        recommender = Recommender(
            embedding_store=embedding_store,
            connection=connection,
        )

        try:
            recommendation_tuples = recommender.recommend(
                fic_id=source["fic_id"]
            )
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

    print(
        f"TIMING | Recommender: {perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    # Stage 4: Convert candidate IDs into full objects with rounded scores
    stage_start = perf_counter()

    recommendation_ids = [fic_id for fic_id, _ in recommendation_tuples]

    resolved_recommendations = FicResolver.resolve_many_from_ids(recommendation_ids)

    score_by_id = {fic_id: score for fic_id, score in recommendation_tuples}

    recommendations = []

    for recommendation in resolved_recommendations:
        fic_id = recommendation["fic_id"]

        recommendation["score"] = round(
            score_by_id[fic_id] * 100,
            1,
        )

        recommendations.append(recommendation)

    print(
        f"TIMING | Recommendation resolution: "
        f"{perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    # Stage 5: Format author and chapter metadata
    stage_start = perf_counter()

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

    print(
        f"TIMING | Response formatting: {perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    # Stage 6: Generate AI explanations for recommendations
    stage_start = perf_counter()

    try:
        explanation_service = ExplanationService()

        explanations = explanation_service.generate_explanations(
            source,
            recommendations,
        )

    except Exception as exc:
        print(f"Explanation generation failed: {exc}", flush=True)

        explanations = [
            "AI explanation temporarily unavailable."
            for _ in recommendations
        ]

    print(
        f"TIMING | AI explanations: {perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    for recommendation, explanation in zip(recommendations, explanations):
        recommendation["explanation"] = explanation

    # Stage 7: Return normalized JSON response payload
    stage_start = perf_counter()

    res = JSONResponse(
        normalize_row({
            "source": source,
            "recommendations": recommendations,
        })
    )

    print(
        f"TIMING | JSON normalization: {perf_counter() - stage_start:.2f}s",
        flush=True,
    )

    print(
        f"TIMING | TOTAL REQUEST: {perf_counter() - total_start:.2f}s",
        flush=True,
    )

    return res