# import uuid
# from enum import StrEnum

# from beanie import Document, UnionDoc, init_beanie
# from motor.motor_asyncio import AsyncIOMotorClient


# class SurveyType(StrEnum):
#     ONE_LINE = "one_line"
#     MULTI_LINE = "multi_line"
#     CHOOSE_ONE = "choose_one"
#     CHOOSE_MULTIPLY = "choose_multiply"


# class ChooseType(StrEnum):
#     CHOOSE_ONE = "choose_one"
#     CHOOSE_MULTIPLY = "choose_multiply"


# class SurveyChoose(Document):
#     value: str
#     choose_type: ChooseType
#     answer: str

#     class Settings:
#         name = "survey_chooses"


# class SurveyBlock(Document):
#     question: str
#     answer_user_id: uuid.UUID | None = None
#     survey_type: SurveyType
#     value: str | None | list[SurveyChoose] = None

#     class Settings:
#         name = "survey_blocks"


# class Survey(Document):
#     name: str
#     image_url: str
#     blocks: list[uuid.UUID]

#     class Settings:
#         name = "surveys"


# async def init():
#     client = AsyncIOMotorClient("mongodb://localhost:27017/voices")

#     await init_beanie(
#         database=client.voices,
#         document_models=[SurveyBlock, SurveyChoose, Survey],
#     )
#     async with await client.start_session() as session:
#         async with session.start_transaction():
#             blocks = [
#                 SurveyBlock(question="Почему?", survey_type=SurveyType.ONE_LINE),
#                 SurveyBlock(question="Объясните почему?", survey_type=SurveyType.MULTI_LINE),
#             ]
#             results = await SurveyBlock.insert_many(blocks)

#             survey = Survey(name="Самое красивое село Ярославской области", image_url="test", blocks=[uuid.uuid4()])
#             await survey.create()


# import asyncio

# asyncio.run(init())
