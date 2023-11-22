from typing import Optional

import aiobotocore.session

from voices.config import settings


class S3Service:

    session: Optional[aiobotocore.session.AioSession] = None
    s3_client: Optional[aiobotocore.session.AioBaseClient] = None

    @classmethod
    async def _get_s3_session(cls) -> aiobotocore.session.AioSession:
        if cls.session is None:
            cls.session = aiobotocore.session.get_session()
        return cls.session

    @classmethod
    async def get_s3_client(cls) -> aiobotocore.session.AioBaseClient:
        if cls.s3_client is None:
            session_ = await cls._get_s3_session()
            cls.s3_client = await session_.create_client(
                region_name=settings.REGION_NAME,
                service_name="s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_AWS_SECRET_ACCESS_KEY,
            ).__aenter__()
        return cls.s3_client

    @classmethod
    async def get_object(cls, img_name: str) -> dict:
        return await cls.s3_client.get_object(Bucket=settings.BUCKET_NAME, Key=img_name)

    @classmethod
    async def put_object(cls, img_name: str, file: bytes) -> dict:
        return await cls.s3_client.put_object(Bucket=settings.BUCKET_NAME, Key=img_name, Body=file)

    @classmethod
    async def delete_object(cls, img_name: str) -> dict:
        return await cls.s3_client.delete_object(Bucket=settings.BUCKET_NAME, Key=img_name)

    @classmethod
    async def close_s3_session(cls) -> None:
        if cls.s3_client is not None:
            await cls.s3_client.close()
            cls.session = None
            cls.s3_client = None
