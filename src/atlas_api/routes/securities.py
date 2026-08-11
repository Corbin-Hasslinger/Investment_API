from fastapi import APIRouter

router = APIRouter(
    prefix="/securities",
    tags=["Securities"],
)