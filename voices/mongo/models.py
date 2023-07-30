import uuid
from enum import StrEnum

from beanie import Document
from pydantic import Field


class BaseDocument(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class SurveyType(StrEnum):
    ONE_LINE = "one_line"
    MULTI_LINE = "multi_line"
    CHOOSE_ONE = "choose_one"
    CHOOSE_MULTIPLY = "choose_multiply"


class ChooseType(StrEnum):
    CHOOSE_ONE = "choose_one"
    CHOOSE_MULTIPLY = "choose_multiply"


class SurveyChoose(BaseDocument):
    value: str
    choose_type: ChooseType
    answer: str

    class Settings:
        name = "survey_chooses"


class SurveyBlock(BaseDocument):
    question: str
    answer_user_id: uuid.UUID | None = None
    survey_type: SurveyType
    value: str | None | list[SurveyChoose] = None

    class Settings:
        name = "survey_blocks"


class Survey(BaseDocument):
    name: str
    image_url: str
    blocks: list[SurveyBlock]

    class Settings:
        name = "surveys"
