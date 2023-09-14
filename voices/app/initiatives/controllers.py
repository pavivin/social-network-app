import uuid

from fastapi import APIRouter, Depends, status

from voices.app.auth.models import User
from voices.app.auth.views import TokenData
from voices.app.core.exceptions import (
    AlreadyVotedError,
    ObjectNotFoundError,
    ObsceneLanguageError,
    ValidationError,
)
from voices.app.core.protocol import PaginationView, Response
from voices.app.core.responses import NotFoundResponse
from voices.app.initiatives.models import Comment, Initiative, InitiativeLike
from voices.app.initiatives.views import (
    CommentListView,
    CommentReplyView,
    CommentRequestView,
    CreateInitiativeVew,
    InitiativeDetailedView,
    InitiativeListView,
    SurveyCreate,
    SurveyVoteView,
)
from voices.auth.jwt_token import JWTBearer
from voices.broker.tasks.notification import EventName, send_notification
from voices.content_filter import content_filter
from voices.db.connection import Transaction
from voices.mongo.models import Survey, SurveyAnswer, SurveyType

router = APIRouter()


@router.get("/initiatives", response_model=Response[InitiativeListView])
async def get_feed(
    category: Initiative.Category | None = None,
    role: User.Role | None = None,
    last_id: uuid.UUID | None = None,
    status: Initiative.Status | None = None,
    city: str = "Ярославль",
    search: str | None = None,
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    user_id = token.sub if token else None
    async with Transaction():
        # TODO: city
        if token:
            user = await User.get_by_id(token.sub)
            city = user.city or "Ярославль"
        feed = await Initiative.get_feed(
            city=city,
            category=category,
            last_id=last_id,
            status=status,
            role=role,
            search=search,
        )
        total = await Initiative.get_feed(
            city=city, category=category, status=status, role=role, search=search, is_total=True
        )
        liked = await InitiativeLike.get_liked(initiative_list=[item.id for item in feed], user_id=user_id)
        set_liked = set(liked)

    response = []
    for initiative in feed:
        initiative.is_liked = initiative.id in set_liked
        response.append(initiative)

    return Response(
        payload=InitiativeListView(
            feed=response,
            pagination=PaginationView(count=len(feed), total=total),
        )
    )


@router.get("/initiatives/favorites", response_model=Response[InitiativeListView])
async def get_favorites(
    last_id: uuid.UUID | None = None,
    token: TokenData | None = Depends(JWTBearer()),
):
    async with Transaction():
        if token:
            user = await User.get_by_id(token.sub)
            city = user.city or "Ярославль"
        else:
            city = "Ярославль"
        feed = await Initiative.get_favorites(city=city, last_id=last_id, user_id=token.sub)
        total = await Initiative.get_favorites(city=city, user_id=token.sub, is_total=True)

    response = []
    for initiative in feed:  # TODO: rewrite
        initiative.is_liked = True
        response.append(initiative)

    return Response(
        payload=InitiativeListView(
            feed=response,
            pagination=PaginationView(count=len(feed), total=total),
        )
    )


@router.get("/initiatives/my", response_model=Response[InitiativeListView])
async def get_my(
    last_id: uuid.UUID | None = None,
    token: TokenData | None = Depends(JWTBearer()),
    user_id: uuid.UUID | None = None,
):
    user_id = user_id or token.sub
    async with Transaction():
        if token:
            user = await User.get_by_id(token.sub)
            city = user.city or "Ярославль"
        else:
            city = "Ярославль"
        feed = await Initiative.get_my(city=city, last_id=last_id, user_id=token.sub)  # TODO: get from user
        total = await Initiative.get_my(city=city, user_id=token.sub, is_total=True)  # TODO: get from user
        liked = await InitiativeLike.get_liked(initiative_list=[item.id for item in feed], user_id=user_id)
        set_liked = set(liked)

    response = []
    for initiative in feed:
        initiative.is_liked = initiative.id in set_liked
        response.append(initiative)

    return Response(
        payload=InitiativeListView(
            feed=response,
            pagination=PaginationView(count=len(feed), total=total),
        )
    )


@router.post("/initiatives", response_model=Response)
async def create_initiative(
    body: CreateInitiativeVew,
    token: TokenData = Depends(JWTBearer()),
):
    async with Transaction():
        if token:
            user = await User.get_by_id(token.sub)
            city = user.city or "Ярославль"
        else:
            city = "Ярославль"
        await Initiative.create(
            city=city,
            user_id=user.id,
            images=body.images,
            category=body.category,
            location=body.location,
            title=body.title,
            main_text=body.main_text,
            event_direction=body.event_direction,
            ar_model=body.ar_model,
        )

    return Response()


@router.get(
    "/initiatives/{initiative_id}",
    response_model=Response[InitiativeDetailedView],
)
async def get_initiative(
    initiative_id: uuid.UUID,
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    user_id = token.sub if token else None
    async with Transaction():
        initiative = await Initiative.select(initiative_id)
        liked = await InitiativeLike.get_liked(initiative_list=[initiative.id], user_id=user_id)
        set_liked = set(liked)

    feed = [InitiativeDetailedView.from_orm(initiative)]
    response = await Survey.get_surveys(feed=feed, token=token, set_liked=set_liked)

    answer = response[0]  # TODO: rewrite

    if answer.survey:
        answer.is_voted = any([[item.user_value for item in block.answer] for block in response[0].survey.blocks])

    return Response(payload=answer)


@router.get(
    "/initiatives/{initiative_id}/comments",
    response_model=Response[CommentListView],
    responses={
        status.HTTP_200_OK: {
            "model": Response[CommentListView],
            "description": "Ok Response",
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
        initiative = await Initiative.get(initiative_id)
        await Comment.post_comment(
            main_text=body.main_text, initiative_id=initiative_id, reply_id=reply_id, user_id=token.sub
        )
        await Initiative.increment_comments_count(initiative_id=initiative_id)

        notification_status = EventName.ANSWERED if reply_id else EventName.COMMENT
        if reply_id:
            comment: Comment = await Comment.get(reply_id)
            user_id_get = comment.user_id
        else:
            user_id_get = initiative.user_id

    send_notification.apply_async(
        kwargs=dict(
            user_id_send=token.sub,
            user_id_get=user_id_get,
            status=notification_status,
            initiative_image=initiative.images[0],
            initiative_id=initiative.id,
        ),
        retry=False,
    )

    return Response()


@router.post("/initiatives/{initiative_id}/like", response_model=Response[CommentReplyView])
async def post_like(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        initiative = await Initiative.get(initiative_id)
        await InitiativeLike.post_like(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_likes_count(initiative_id=initiative_id, count=1)

    send_notification.apply_async(
        kwargs=dict(
            user_id_send=token.sub,
            user_id_get=initiative.user_id,
            status=EventName.LIKE,
            initiative_image=initiative.images[0],
            initiative_id=initiative.id,
        ),
        retry=False,
    )

    return Response()


@router.post("/initiatives/{initiative_id}/unlike", response_model=Response[CommentReplyView])
async def post_unlike(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Initiative.get(initiative_id)
        await InitiativeLike.delete_like(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_likes_count(initiative_id=initiative_id, count=-1)

    return Response()


@router.post("/initiatives/{initiative_id}/survey", response_model=Response)
async def create_survey(initiative_id: uuid.UUID, body: SurveyCreate, _: TokenData = Depends(JWTBearer())):
    survey = Survey(
        id=initiative_id,
        name=body.name,
        image_url=body.image_url,
        blocks=body.blocks,
    )
    await survey.create()
    return Response()


@router.put("/initiatives/{initiative_id}/vote", response_model=Response)
async def vote_initiative(initiative_id: uuid.UUID, body: SurveyVoteView, token: TokenData = Depends(JWTBearer())):
    survey = await Survey.get(initiative_id)  # TODO: to background
    if not survey:
        raise ObjectNotFoundError

    existing_answer = await SurveyAnswer.find(
        SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative_id
    ).first_or_none()

    if existing_answer:  # TODO: create composite FK
        raise AlreadyVotedError

    answer = SurveyAnswer(survey_id=initiative_id, user_id=token.sub, blocks=body.blocks)

    survey.vote_count += 1

    for i, block in enumerate(answer.blocks):
        for j, option in enumerate(block.answer):
            if option.value is not None:
                try:
                    survey.blocks[i].answer[j].vote_count += 1
                    survey.blocks[i].answer[j].vote_percent = int((option.vote_count / survey.vote_count) * 100)
                except KeyError:
                    raise ValidationError(message="Not enough values in answer")

            if survey.blocks[i].survey_type == SurveyType.CHOOSE_ONE:
                option.value = bool(option.value)

    await answer.create()
    await survey.save()

    return Response()
