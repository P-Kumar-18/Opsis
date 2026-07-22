from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from . import templates as loc


router = APIRouter()

templates = Jinja2Templates(directory=loc)


@router.get("/about")
async def about(request: Request):
    """Render the About page HTML template."""
    return templates.TemplateResponse(request=request, name="about.html")