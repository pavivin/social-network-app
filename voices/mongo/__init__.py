from motor.motor_asyncio import AsyncIOMotorClient

from voices.config import settings

if settings.DEBUG:  # TODO: remove
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
else:
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL, replicaset=settings.MONGO_REPLICA_SET)
