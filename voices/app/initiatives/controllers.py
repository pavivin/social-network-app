import uuid

from fastapi import APIRouter, Depends

from voices.app.auth.views import TokenData
from voices.app.initiatives.models import Comment, Initiative
from voices.app.initiatives.views import (
    CommentListView,
    CommentReplyView,
    CommentRequestView,
    InitiativeListView,
    InitiativeView,
)
from voices.auth.jwt_token import JWTBearer
from voices.content_filter import content_filter
from voices.db.connection import Transaction
from voices.exceptions import ObsceneLanguageError
from voices.protocol import PaginationView, Response

router = APIRouter()


@router.get("/initiatives", response_model=Response[InitiativeListView])
async def get_feed(category: Initiative.Category | None = None, last_id: uuid.UUID = None):
    async with Transaction():
        feed = await Initiative.get_feed(city="test", category=category, last_id=last_id)

    return Response(
        payload=InitiativeListView(
            feed=[InitiativeView.from_orm(initiative) for initiative in feed],
            pagination=PaginationView(total=len(feed)),
        )
    )


@router.get("/initiatives/{initiative_id}/comments", response_model=Response[CommentListView])
async def get_comments(initiative_id: uuid.UUID, last_id: uuid.UUID = None):
    async with Transaction():
        await Initiative.get(initiative_id)  # raises 404
        comments = await Comment.get_comments(initiative_id=initiative_id, last_id=last_id)

        return Response(
            payload=CommentListView(
                comments=[CommentReplyView.from_orm(item) for item in comments],
                pagination=PaginationView(total=len(comments)),
            )
        )


@router.post("/initiatives/{initiative_id}/comments", response_model=Response[CommentReplyView])
async def post_comment(
    body: CommentRequestView,
    initiative_id: uuid.UUID,
    token: TokenData = Depends(JWTBearer()),
    reply_id: uuid.UUID | None = None,
):
    if content_filter.is_obscene(body.main_text):
        raise ObsceneLanguageError

    async with Transaction():
        await Initiative.get(initiative_id)
        await Comment.post_comment(
            main_text=body.main_text, initiative_id=initiative_id, reply_id=reply_id, user_id=token.sub
        )

    return Response()
