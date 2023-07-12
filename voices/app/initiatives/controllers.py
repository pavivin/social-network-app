import uuid

from fastapi import APIRouter, Depends, status

from voices.app.auth.models import User
from voices.app.auth.views import TokenData
from voices.app.core.exceptions import ObsceneLanguageError
from voices.app.core.protocol import PaginationView, Response
from voices.app.core.responses import BadRequestResponse, NotFoundResponse
from voices.app.initiatives.models import Comment, Initiative, InitiativeLike
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

router = APIRouter()


@router.get("/initiatives", response_model=Response[InitiativeListView])
async def get_feed(
    category: Initiative.Category | None = None,
    role: User.Role | None = None,
    last_id: uuid.UUID | None = None,
    status: Initiative.Status | None = None,
    city: str = "test",
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    async with Transaction():
        # TODO: city
        feed = await Initiative.get_feed(
            city=city,
            category=category,
            last_id=last_id,
            status=status,
            role=role,
        )

    return Response(
        payload=InitiativeListView(
            feed=[InitiativeView.from_orm(initiative) for initiative in feed],
            pagination=PaginationView(total=len(feed)),
        )
    )


@router.get("/initiatives", response_model=Response[InitiativeListView])
async def create_initiative(
    _: TokenData | None = Depends(JWTBearer()),
):
    async with Transaction():
        # TODO: city
        await Initiative.create()

    return Response()


@router.get(
    "/initiatives/{initiative_id}/comments",
    response_model=Response[CommentListView],
    responses={
        status.HTTP_200_OK: {
            "model": Response[CommentListView],
            "description": "Ok Response",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": BadRequestResponse,
            "description": "Atributes are not correct or comment text is not appropriate",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundResponse,
            "description": "Initiative with id not found",
        },
    },
)
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
        await Initiative.increment_comments_count(initiative_id=initiative_id)

    return Response()


@router.post("/initiatives/{initiative_id}/like", response_model=Response[CommentReplyView])
async def post_like(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Initiative.get(initiative_id)
        await InitiativeLike.post_like(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_likes_count(initiative_id=initiative_id, count=1)

    return Response()


@router.post("/initiatives/{initiative_id}/unlike", response_model=Response[CommentReplyView])
async def post_unlike(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Initiative.get(initiative_id)
        await InitiativeLike.delete_like(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_likes_count(initiative_id=initiative_id, count=-1)

    return Response()
