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
            feed=[
                InitiativeView(
                    user_id=initiative.user_id,
                    city=initiative.city,
                    images=initiative.images,
                    category=initiative.category,
                    location=initiative.location,
                    title=initiative.title,
                    main_text=initiative.main_text,
                )
                for initiative in feed
            ],
        )
    )
