from motor.motor_asyncio import AsyncIOMotorClient

from voices.config import settings

mongo_client = AsyncIOMotorClient(settings.MONGO_URL, replicaset=settings.MONGO_REPLICA_SET)
