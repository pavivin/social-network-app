import uuid
from datetime import date, datetime

import pydantic
from pydantic import AnyUrl, Field, root_validator

from voices.app.core.exceptions import ValidationError
from voices.app.core.protocol import BaseModel, GeometryPoint, PaginationView
from voices.mongo.models import SurveyType

from .models import Initiative


class SurveyChooseCreateView(BaseModel):
    value: str | None = None


class SurveyChooseView(BaseModel):
    value: str | None = None
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
    id: str
    first_name: str = "unknown"
    last_name: str = "user"
    image_url: str | None

    @pydantic.validator("id", pre=True)
    def convert_id(cls, v, values, **kwargs):
        return str(v)

    @pydantic.validator("image_url", pre=True)
    def prepare_public_file(cls, v: str, values):
        if "min" in v:
            return v
        filename = v.split("/")[-1]
        name, file_ext = filename.split(".")
        return f"https://storage.yandexcloud.net/my-city/{name}-min.{file_ext}"


class InitiativeView(BaseModel):
    id: str
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
    supports_count: int
    created_at: str | datetime
    from_date: date | None
    to_date: date | None
    is_liked: bool = False
    is_supported: bool = False
    tags: list | None
    survey: SurveyView | None = None
    ar_model: str | None
    address: str | None
    event_direction: str | None

    @pydantic.validator("id", pre=True)
    def convert_id(cls, v: uuid.UUID, values, **kwargs):
        return str(v)

    @pydantic.validator("created_at", pre=True)
    def convert_datetime(cls, v: datetime, values, **kwargs):
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            return v
        raise ValidationError

    @pydantic.validator("tags", pre=True)
    def convert_tags(cls, v, values: dict, **kwargs):
        tags = [{"type": Initiative.Status.ACTIVE, "label": "Активно", "icon": None}]  # TODO: archive

        from_date, to_date = values["from_date"], values["to_date"]
        if from_date and to_date:
            from_date = from_date.strftime("%d.%m.%Y")
            to_date = to_date.strftime("%d.%m.%Y")

            tag = {
                "type": Initiative.TypeTagsEnum.DEFAULT,
                "label": f"{from_date} - {to_date}",
                "icon": Initiative.IconTagsEnum.DATE,
            }
            tags.append(tag)

        survey = values.get("survey")  # TODO: count of questions, is survey exists
        if survey:
            tag = {
                "type": Initiative.TypeTagsEnum.DEFAULT,
                "label": "Голосование",
                "icon": Initiative.IconTagsEnum.QUESTIONS,
            }

        ar_model = values.get("ar_model")
        if ar_model:
            tag = {"type": Initiative.TypeTagsEnum.DEFAULT, "label": "AR", "icon": None}

        address = values.get("address")
        if address:
            tag = {"type": Initiative.TypeTagsEnum.DEFAULT, "label": address, "icon": Initiative.IconTagsEnum.GEO}

        event_direction = values.get("event_direction")
        if event_direction:
            tag = {"type": Initiative.TypeTagsEnum.DEFAULT, "label": event_direction, "icon": None}

        return tags


class InitiativeDetailedView(InitiativeView):
    is_liked: bool = False
    is_supported: bool = False
    is_voted: bool = False
    ar_model: str | None

    @pydantic.validator("id", pre=True)
    def convert_id(cls, v: uuid.UUID, values, **kwargs):
        return str(v)


class InitiativeListView(BaseModel):
    feed: list[InitiativeView]
    pagination: PaginationView


class CommentView(BaseModel):
    id: str
    created_at: str | datetime
    user: UserView
    main_text: str

    @pydantic.validator("id", pre=True)
    def convert_id(cls, v: uuid.UUID, values, **kwargs):
        return str(v)


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
