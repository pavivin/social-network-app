from fastapi import APIRouter, Depends, Query

from voices.app.auth.views import SearchListView, TokenData
from voices.app.core.protocol import Response
from voices.app.friends.models import Friend, User
from voices.auth.jwt_token import JWTBearer
from voices.db.connection import Transaction

router = APIRouter()


@router.get("/friends", response_model=Response[SearchListView])
async def search_by_pattern(
    pattern: str | None = Query(default=None, min_length=1), token: TokenData = Depends(JWTBearer())
):
    async with Transaction():
        if not pattern:
            response = await Friend.get_friends(user_id=token.sub)
            users = [item.friend for item in response]
        else:
            users = await User.search_by_pattern(pattern=pattern)

    return Response(payload=SearchListView(users=users))


@router.patch("/friends/{friend_id}/add", response_model=Response[SearchListView])
async def add_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Friend.add_friend(user_id=token.sub, friend_id=friend_id)

    return Response()


@router.patch("/friends/{friend_id}/approve", response_model=Response[SearchListView])
async def approve_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Friend.approve_friend(user_id=token.sub, friend_id=friend_id)

    return Response()


@router.patch("/friends/{friend_id}/remove", response_model=Response[SearchListView])
async def remove_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Friend.remove_friend(user_id=token.sub, friend_id=friend_id)

    return Response()
