from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError

from voices.app.auth.views import TokenData
from voices.app.core.exceptions import FriendAlreadyAddedError
from voices.app.core.protocol import Response
from voices.app.friends.models import Friend, User
from voices.app.friends.views import FriendListView, PaginationView
from voices.auth.jwt_token import JWTBearer
from voices.broker.tasks.notification import EventName, send_notification
from voices.db.connection import Transaction

router = APIRouter()


@router.get("/users", response_model=Response[FriendListView])
async def get_users(
    pattern: str | None = None,
    last_id: str | None = None,
    token: TokenData = Depends(JWTBearer()),
):
    async with Transaction():
        users = await User.search_by_pattern(pattern=pattern, last_id=last_id)  # TODO: return total in the same def
        total = await User.search_by_pattern(pattern=pattern, is_total=True)

    return Response(
        payload=FriendListView(
            users=users,
            pagination=PaginationView(count=len(users), total=total),
        )
    )


@router.get("/friends", response_model=Response[FriendListView])
async def search_by_pattern(
    pattern: str | None = Query(default=None, min_length=1),
    last_id: str | None = None,
    token: TokenData = Depends(JWTBearer()),
):
    async with Transaction():
        users = await Friend.get_friends(user_id=token.sub, pattern=pattern)
        users = [user.friend if user.friend_id != UUID(token.sub) else user.user for user in users]
        total = await Friend.get_friends(user_id=token.sub, is_total=True)

    return Response(
        payload=FriendListView(
            users=users,
            pagination=PaginationView(count=len(users), total=total),
        )
    )


@router.patch("/friends/{friend_id}/add", response_model=Response)
async def add_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        try:
            await Friend.add_friend(user_id=token.sub, friend_id=friend_id)
        except IntegrityError:
            raise FriendAlreadyAddedError

    send_notification.apply_async(
        kwargs=dict(user_id_send=token.sub, user_id_get=friend_id, status=EventName.REQUEST_FRENDS),
        retry=False,
    )

    return Response()


@router.patch("/friends/{friend_id}/approve", response_model=Response)
async def approve_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Friend.approve_friend(user_id=token.sub, friend_id=friend_id)

    send_notification.apply_async(
        kwargs=dict(user_id_send=token.sub, user_id_get=friend_id, status=EventName.ACCEPT_FRENDS),
        retry=False,
    )

    return Response()


@router.patch("/friends/{friend_id}/remove", response_model=Response)
async def remove_friend(friend_id: str, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Friend.remove_friend(user_id=token.sub, friend_id=friend_id)

    return Response()
