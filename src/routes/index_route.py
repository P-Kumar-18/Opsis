from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from . import templates as loc

router = APIRouter()

templates = Jinja2Templates(
    directory = loc
)


@router.get("/")
async def index(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )