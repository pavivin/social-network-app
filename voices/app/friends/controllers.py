from fastapi import APIRouter, Depends, Query

from voices.app.auth.views import SearchListView, TokenData
from voices.app.core.protocol import Response
from voices.app.friends.models import Friend, User
from voices.auth.jwt_token import JWTBearer
from voices.db.connection import Transaction

router = APIRouter()


@router.get("/friends", response_model=Response[SearchListView])
async def search_by_pattern(
    pattern: str | None = Query(default=None, min_length=2), token: TokenData = Depends(JWTBearer())
):
    async with Transaction():
        if not pattern:
            response = await Friend.get_friends(user_id=token.sub)
            users = [item.friend for item in response]
        else:
            users = await User.search_by_pattern(pattern=pattern)

    return Response(payload=SearchListView(users=users))
