from fastapi import APIRouter

from voices.protocol import Response

router = APIRouter()


@router.get(
    "/healthz",
    response_model=Response,
)
async def get_healthcheck():
    return Response()
