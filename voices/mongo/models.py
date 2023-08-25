import uuid
from enum import StrEnum

from beanie import Document
from pydantic import Field
from uuid_extensions import uuid7


class BaseDocument(Document):
    id: uuid.UUID = Field(default_factory=uuid7)


class SurveyType(StrEnum):
    ONE_LINE = "one_line"
    MULTI_LINE = "multi_line"
    CHOOSE_ONE = "choose_one"
    CHOOSE_MULTIPLY = "choose_multiply"


class SurveyChoose(BaseDocument):
    user_value: str | None = None
    value: str
    vote_count: int = 0
    vote_percent: int = 0

    class Settings:
        name = "survey_chooses"


class SurveyBlock(BaseDocument):
    question: str
    survey_type: SurveyType
    answer: list[SurveyChoose]


class SurveyAnswer(BaseDocument):
    survey_id: uuid.UUID
    user_id: uuid.UUID
    blocks: list[SurveyBlock]

    class Settings:
        name = "survey_answers"


class Survey(BaseDocument):
    name: str
    image_url: str
    blocks: list[SurveyBlock]
    vote_count: int = 0

    @classmethod
    async def get_surveys(cls, feed, token, set_liked=None):
        response = []
        for initiative in feed:
            initiative.is_liked = initiative.id in set_liked if set_liked else True
            initiative.survey = await Survey.get(initiative.id)
            if token:
                answer = await SurveyAnswer.find(
                    SurveyAnswer.user_id == uuid.UUID(token.sub), SurveyAnswer.survey_id == initiative.id
                ).first_or_none()
                if answer:
                    for i, item in enumerate(answer.blocks):
                        for j, choose in enumerate(item.answer):
                            initiative.survey.blocks[i].answer[j].user_value = choose.value

            response.append(initiative)
        return response

    class Settings:
        name = "surveys"
