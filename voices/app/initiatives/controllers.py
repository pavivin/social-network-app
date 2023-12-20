import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status

from voices.app.auth.models import User
from voices.app.auth.views import TokenData
from voices.app.core.exceptions import (  # NeedEmailConfirmation,
    AlreadyVotedError,
    ForbiddenError,
    ObjectNotFoundError,
    ObsceneLanguageError,
    ValidationError,
)
from voices.app.core.protocol import PaginationView, Response
from voices.app.core.responses import (
    BadRequestResponse,
    ForbiddenResponse,
    NotFoundResponse,
)
from voices.app.initiatives.models import (
    Comment,
    Initiative,
    InitiativeLike,
    InitiativeSupport,
)
from voices.app.initiatives.views import (
    CommentListView,
    CommentReplyView,
    CommentRequestView,
    CreateInitiativeVew,
    InitiativeDetailedView,
    InitiativeListView,
    InitiativeView,
    SurveyCreate,
    SurveyView,
    SurveyVoteView,
)
from voices.auth.jwt_token import JWTBearer
from voices.broker.tasks.notification import EventName, send_notification
from voices.config import settings
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
    search: str | None = None,
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    user_id = token.sub if token else None
    city = settings.DEFAULT_CITY
    async with Transaction():
        if token:
            user = await User.get_by_id(token.sub)  # TODO: get from token
            city = user.city or settings.DEFAULT_CITY

        # cache prefix: i
        # cache_key = ( # cache works but breaks likes
        #     f"i:{CITY_MAPPING[city]}:{user_id or ''}:{last_id or ''}:{category or ''}:{search or ''}:{role or ''}"
        # )
        # cached = await Redis.con.get(cache_key)
        # cached_total = await Redis.con.get(
        #     f"it:{CITY_MAPPING[city]}:{last_id or ''}:{category or ''}:{search or ''}:{role or ''}"
        # )  # TODO: to one call
        # if cached and cached_total:
        #     dict_initiatives = json.loads(cached)
        #     return Response(
        #         payload=InitiativeListView(
        #             feed=[InitiativeView.parse_obj(item) for item in dict_initiatives],
        #             pagination=PaginationView(count=len(dict_initiatives), total=cached_total),
        #         )
        #     )

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
        set_liked = set(map(str, liked))
        supported = await InitiativeSupport.get_supported(initiative_list=[item.id for item in feed], user_id=user_id)
        set_supported = set(supported)

    response: list[InitiativeView] = []
    for initiative in feed:
        initiative_view = InitiativeView.from_orm(initiative)
        initiative_view.is_liked = initiative_view.id in set_liked
        initiative_view.is_supported = initiative_view.id in set_supported
        survey = await Survey.get(str(initiative_view.id))  # TODO: get back to UUID
        if survey:
            initiative_view.survey = survey
            existing_answer = await SurveyAnswer.find(
                SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative_view.id
            ).first_or_none()
            initiative_view.is_voted = bool(existing_answer)
        response.append(initiative_view)

    # dict_initiatives = []
    # for item in response:
    #     dict_item = json.loads(json.dumps(item, default=lambda o: getattr(o, "__dict__", str(o))))
    #     dict_initiatives.append(dict_item)

    # await Redis.con.set(name=cache_key, value=json.dumps(dict_initiatives), ex=60)
    # await Redis.con.set(name=f"it:{CITY_MAPPING[city]}", value=total, ex=60)

    return Response(
        payload=InitiativeListView(
            feed=response,
            pagination=PaginationView(count=len(feed), total=total),
        )
    )


@router.get("/initiatives/actual", response_model=Response[InitiativeListView])
async def get_feed_actual(
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    city = settings.DEFAULT_CITY
    async with Transaction():
        if token:
            user = await User.get_by_id(token.sub)  # TODO: city number to token (e.g. 1 - Yaroslavl)
            city = user.city or settings.DEFAULT_CITY
        feed = await Initiative.get_actual(city=city)
        total = await Initiative.get_actual(city=city, is_total=True)

    return Response(
        payload=InitiativeListView(
            feed=feed,
            pagination=PaginationView(count=len(feed), total=total),
        )
    )


@router.get("/initiatives/maps", response_model=Response[InitiativeListView])
async def get_feed_maps(
    category: Initiative.Category | None = None,
    role: User.Role | None = None,
    status: Initiative.Status | None = None,
    search: str | None = None,
    token: TokenData | None = Depends(JWTBearer(required=False)),
):
    user_id = token.sub if token else None
    city = settings.DEFAULT_CITY
    async with Transaction():
        # TODO: city
        if token:
            user = await User.get_by_id(token.sub)
            city = user.city or settings.DEFAULT_CITY
        feed = await Initiative.get_feed(
            city=city,
            category=category,
            status=status,
            role=role,
            search=search,
            is_maps=True,
        )
        total = await Initiative.get_feed(
            city=city, category=category, status=status, role=role, search=search, is_total=True
        )
        liked = await InitiativeLike.get_liked(initiative_list=[item.id for item in feed], user_id=user_id)
        set_liked = set(map(str, liked))
        supported = await InitiativeSupport.get_supported(initiative_list=[item.id for item in feed], user_id=user_id)
        set_supported = set(map(str, supported))

    response = []
    for initiative in feed:
        initiative_view = InitiativeView.from_orm(initiative)
        initiative_view.is_liked = initiative_view.id in set_liked
        initiative_view.is_supported = initiative_view.id in set_supported
        response.append(initiative_view)

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
            city = user.city or settings.DEFAULT_CITY
        else:
            city = settings.DEFAULT_CITY
        feed = await Initiative.get_favorites(city=city, last_id=last_id, user_id=token.sub)
        total = await Initiative.get_favorites(city=city, user_id=token.sub, is_total=True)

    response = []
    for initiative in feed:  # TODO: rewrite
        initiative_view = InitiativeView.from_orm(initiative)
        initiative_view.is_liked = True
        initiative_view.survey = await Survey.get(str(initiative_view.id))
        response.append(initiative_view)

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
            city = user.city or settings.DEFAULT_CITY
        else:
            city = settings.DEFAULT_CITY
        feed = await Initiative.get_my(city=city, last_id=last_id, user_id=user_id)
        total = await Initiative.get_my(city=city, user_id=user_id, is_total=True)
        liked = await InitiativeLike.get_liked(initiative_list=[item.id for item in feed], user_id=user_id)
        set_liked = set(map(str, liked))
        supported = await InitiativeSupport.get_supported(initiative_list=[item.id for item in feed], user_id=user_id)
        set_supported = set(map(str, supported))

    response = []
    for initiative in feed:
        initiative_view = InitiativeView.from_orm(initiative)
        initiative_view.is_liked = initiative_view.id in set_liked
        initiative_view.is_supported = initiative_view.id in set_supported
        initiative_view.survey = await Survey.get(str(initiative_view.id))
        if initiative_view.survey and token:
            existing_answer = await SurveyAnswer.find(
                SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative_view.id
            ).first_or_none()
            initiative_view.is_voted = bool(existing_answer)
        response.append(initiative_view)

    return Response(
        payload=InitiativeListView(
            feed=feed,
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
            city = user.city or settings.DEFAULT_CITY
        else:
            city = settings.DEFAULT_CITY

        # if not user.email_approved:
        #     raise NeedEmailConfirmation

        initiative_id = await Initiative.create(
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

    send_notification.apply_async(
        kwargs=dict(
            user_id_send=token.sub,
            user_id_get=token.sub,
            status=EventName.POST_CREATED,
            initiative_image=body.images[0],
            initiative_id=initiative_id,
        ),
        retry=False,
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
        set_liked = set(map(str, liked))
        supported = await InitiativeSupport.get_supported(initiative_list=[initiative.id], user_id=user_id)
        set_supported = set(map(str, supported))

    feed = [InitiativeDetailedView.from_orm(initiative)]
    response = await Survey.get_surveys(feed=feed, token=token, set_liked=set_liked, set_supported=set_supported)

    answer = response[0]  # TODO: rewrite

    if answer.survey and token:
        existing_answer = await SurveyAnswer.find(
            SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative_id
        ).first_or_none()
        answer.is_voted = bool(existing_answer)
        if existing_answer:
            for i, item in enumerate(existing_answer.blocks):
                for j, choose in enumerate(item.answer):
                    answer.survey.blocks[i].answer[j].user_value = choose.value

    return Response(payload=answer)


@router.delete(
    "/initiatives/{initiative_id}",
    response_model=Response,
    responses={
        status.HTTP_200_OK: {  # TODO: all routes with responses schema
            "model": Response,
            "description": "Ok Response",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": BadRequestResponse,
            "description": "Already Deleted",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ForbiddenResponse,
            "description": "Forbidden",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotFoundResponse,
            "description": "Initiative with id not found",
        },
    },
)
async def delete_initiative(
    initiative_id: uuid.UUID,
    token: TokenData = Depends(JWTBearer()),
):
    async with Transaction():
        initiative = await Initiative.get(initiative_id)  # raises 404
        if initiative.user_id.hex != token.sub:
            raise ForbiddenError
        initiative.deleted_at = datetime.now()

    return Response()


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
        initiative = await Initiative.get(initiative_id)  # raises 404
        comments = await Comment.get_comments(initiative_id=initiative_id, last_id=last_id)
        for comment in comments:
            replies = [reply for reply in comment.replies if not reply.deleted_at]
            comment.replies = replies

    return Response(
        payload=CommentListView(
            comments=[CommentReplyView.from_orm(item) for item in comments],
            pagination=PaginationView(total=initiative.comments_count, count=len(comments)),
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
        if reply_id:
            reply_comment = await Comment.get(reply_id)
            if reply_comment.parent_id:
                reply_id = reply_comment.parent_id
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

    if token.sub != user_id_get:
        send_notification.apply_async(
            kwargs=dict(
                user_id_send=token.sub,
                user_id_get=str(user_id_get),
                status=notification_status,
                initiative_image=initiative.images[0],
                initiative_id=initiative.id,
            ),
            retry=False,
        )

    return Response()


@router.delete("/initiatives/{initiative_id}/comments/{comment_id}", response_model=Response[CommentReplyView])
async def delete_comment(
    initiative_id: uuid.UUID,
    comment_id: uuid.UUID,
    token: TokenData = Depends(JWTBearer()),
):
    async with Transaction():
        comment = await Comment.get(comment_id)
        if comment.user_id.hex != token.sub:
            raise ForbiddenError()
        await Comment.delete_comment(comment_id=comment_id)
        await Initiative.decrement_comments_count(initiative_id=initiative_id)

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


@router.post("/initiatives/{initiative_id}/support", response_model=Response[CommentReplyView])
async def post_support(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Initiative.get(initiative_id)
        await InitiativeSupport.post_support(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_supports_count(initiative_id=initiative_id, count=1)

    return Response()


@router.post("/initiatives/{initiative_id}/unsupport", response_model=Response[CommentReplyView])
async def post_unsupport(initiative_id: uuid.UUID, token: TokenData = Depends(JWTBearer())):
    async with Transaction():
        await Initiative.get(initiative_id)
        await InitiativeSupport.delete_support(initiative_id=initiative_id, user_id=token.sub)
        await Initiative.update_supports_count(initiative_id=initiative_id, count=-1)

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


@router.delete("/initiatives/{initiative_id}/survey", response_model=Response)
async def delete_survey(initiative_id: uuid.UUID, _: TokenData = Depends(JWTBearer())):
    await Survey.find(Survey.id == str(initiative_id)).delete()
    await SurveyAnswer.find(SurveyAnswer.survey_id == str(initiative_id)).delete()
    await SurveyAnswer.find(SurveyAnswer.survey_id == initiative_id).delete()
    return Response()


@router.put("/initiatives/{initiative_id}/vote", response_model=Response[SurveyView])
async def vote_initiative(initiative_id: uuid.UUID, body: SurveyVoteView, token: TokenData = Depends(JWTBearer())):
    survey = await Survey.get(str(initiative_id))  # TODO: to background
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
            try:
                if option.value is not None:
                    survey.blocks[i].answer[j].vote_count += 1
                    survey.blocks[i].answer[j].vote_percent = int(
                        ((survey.blocks[i].answer[j].vote_count) / survey.vote_count) * 100
                    )
                else:
                    survey.blocks[i].answer[j].vote_percent = int(
                        ((survey.blocks[i].answer[j].vote_count) / survey.vote_count) * 100
                    )
            except KeyError:
                raise ValidationError(message="Not enough values in answer")

            if survey.blocks[i].survey_type == SurveyType.CHOOSE_ONE:
                option.value = bool(option.value)

    await answer.create()
    await survey.save()

    answer = await SurveyAnswer.find(
        SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative_id
    ).first_or_none()
    if answer:
        for i, item in enumerate(answer.blocks):
            for j, choose in enumerate(item.answer):
                survey.blocks[i].answer[j].user_value = choose.value

    return Response(payload=survey)
