import uuid
from datetime import date, datetime

from pydantic import AnyUrl, Field, root_validator

from voices.app.core.exceptions import ValidationError
from voices.app.core.protocol import BaseModel, GeometryPoint, PaginationView
from voices.mongo.models import SurveyType

from .models import Initiative


class SurveyChooseCreateView(BaseModel):
    value: str = None


class SurveyChooseView(BaseModel):
    value: str
    user_value: str = None
    vote_count: int = 0
    vote_percent: int = 0


class SurveyBlockView(BaseModel):
    question: str
    survey_type: SurveyType
    answer: list[SurveyChooseView]


class SurveyBlockCreateView(BaseModel):
    question: str
    survey_type: SurveyType
    answer: list[SurveyChooseCreateView]


class SurveyVoteView(BaseModel):
    blocks: list[SurveyBlockCreateView]


class SurveyCreate(BaseModel):
    name: str
    image_url: str | None
    blocks: list[SurveyBlockCreateView]


class SurveyView(BaseModel):
    name: str
    image_url: str
    blocks: list[SurveyBlockView]
    blocks_count: int = 0
    vote_count: int = 0

    @root_validator(pre=True)
    def set_blocks_count(cls, data: dict):
        data["blocks_count"] = len(data["blocks"])
        return data


class UserView(BaseModel):
    id: uuid.UUID | str
    first_name: str = "unknown"
    last_name: str = "user"
    image_url: str | None


class InitiativeView(BaseModel):
    id: str | uuid.UUID
    user: UserView
    city: str
    images: list | dict | None
    category: Initiative.Category
    location: GeometryPoint | None
    title: str
    main_text: str
    likes_count: int
    comments_count: int
    reposts_count: int
    created_at: datetime
    is_liked: bool = False
    tags: list[str] | None
    survey: SurveyView | None = None


class InitiativeDetailedView(InitiativeView):
    id: str | uuid.UUID
    user: UserView
    city: str
    images: list | dict | None
    category: Initiative.Category
    location: GeometryPoint | None
    title: str
    main_text: str
    likes_count: int
    comments_count: int
    reposts_count: int
    created_at: datetime
    survey: SurveyView | None = None
    is_liked: bool = False
    is_voted: bool = False
    tags: list[str] | None
    ar_model: str | None


class InitiativeListView(BaseModel):
    feed: list[InitiativeView]
    pagination: PaginationView


class CommentView(BaseModel):
    id: uuid.UUID
    created_at: str | datetime
    user: UserView
    main_text: str


class CommentReplyView(CommentView):
    replies: list[CommentView] = []


class CommentListView(BaseModel):
    comments: list[CommentReplyView]
    pagination: PaginationView


class CommentRequestView(BaseModel):
    main_text: str


class CreateInitiativeVew(BaseModel):
    images: list[AnyUrl] | None
    category: Initiative.CitizenCategory
    location: GeometryPoint | None = Field(examples=[{"lat": 57.624804, "lon": 39.885072}])
    title: str
    main_text: str
    from_date: date | None
    to_date: date | None
    ar_model: AnyUrl | None
    event_direction: str | None

    @root_validator(pre=True)
    def set_blocks_count(cls, data: dict):
        if (
            data["category"] in (Initiative.CitizenCategory.BUILDING, Initiative.CitizenCategory.DECIDE_TOGETHER)
            and not data["location"]
        ):
            raise ValidationError("Location not set")
        return data
