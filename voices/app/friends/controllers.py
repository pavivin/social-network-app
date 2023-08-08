from fastapi import APIRouter, Query

from voices.app.auth.models import User
from voices.app.auth.views import SearchListView
from voices.app.core.protocol import Response
from voices.db.connection import Transaction

router = APIRouter()


@router.get("/friends", response_model=Response[SearchListView])
async def search_by_pattern(pattern: str = Query(min_length=2)):
    async with Transaction():
        users = await User.search_by_pattern(pattern=pattern)

    return Response(payload=SearchListView(users=users))
