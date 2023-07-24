import asyncio
import uuid
from enum import StrEnum

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

client = AsyncIOMotorClient("mongodb://localhost:27017/voices")


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


async def init():
    await init_beanie(
        database=client.voices,
        document_models=[SurveyBlock, SurveyChoose, Survey],
    )
    async with await client.start_session() as session:
        async with session.start_transaction():
            blocks = [
                SurveyBlock(question="Почему?", survey_type=SurveyType.ONE_LINE),
                SurveyBlock(question="Объясните почему?", survey_type=SurveyType.MULTI_LINE),
            ]

            survey = Survey(name="Самое красивое село Ярославской области", image_url="test", blocks=blocks)
            await survey.create()


async def select_survey(survey_id: uuid.UUID = "8f870913-8c67-4c9f-87c3-228e89ae8907"):
    await init_beanie(
        database=client.voices,
        document_models=[SurveyBlock, SurveyChoose, Survey],
    )

    survey = await Survey.get(survey_id)
    survey


asyncio.run(select_survey())
