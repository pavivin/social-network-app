from fastapi import APIRouter

from voices.app.initiatives.models import Initiative
from voices.app.initiatives.views import InitiativeListView, InitiativeView
from voices.db.connection import Transaction
from voices.protocol import Response

router = APIRouter()


@router.post("/feed", response_model=Response[InitiativeListView])
async def get_feed(category: Initiative.Category | None = None):
    async with Transaction():
        feed = await Initiative.get_feed(city="test", category=category)

    return Response(
        payload=InitiativeListView(
            feed=[InitiativeView.from_orm(initiative) for initiative in feed],
        )
    )
