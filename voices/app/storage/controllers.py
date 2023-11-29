import io
import os

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from uuid_extensions import uuid7

from voices.app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from voices.app.core.protocol import Response
from voices.app.storage.s3 import S3Service
from voices.config import settings
import webp


class Storage:
    @classmethod
    async def create(cls, file_ext: str, file_data: bytes) -> str:
        filename = uuid7(as_type="hex")

        if file_ext in settings.ALLOWED_PHOTO_TYPES:
            img = Image.open(io.BytesIO(file_data))

            pic = webp.WebPPicture.from_pil(img)
            config = webp.WebPConfig.new(lossless=True)

            max_webp_data = bytes(pic.encode(config).buffer())
            min_config = webp.WebPConfig.new(quality=10)
            min_webp_data = bytes(pic.encode(min_config).buffer())
            max_image_path = f"{filename}.webp"
            mini_image_path = f"{filename}-min.webp"
            await S3Service.put_object(img_name=max_image_path, file=max_webp_data)  # TODO: to asyncio.gather
            await S3Service.put_object(img_name=mini_image_path, file=min_webp_data)

            s3_filepath = max_image_path

        else:
            s3_filepath = f"{filename}.{file_ext}"
            await S3Service.put_object(img_name=s3_filepath, file=file_data)

        full_path = f"https://storage.yandexcloud.net/my-city/{s3_filepath}"
        return full_path


router = APIRouter()


@router.post("/storage", response_model=Response)
async def add_file(upload_file: UploadFile):
    file_ext = upload_file.filename.split(".")[-1].lower()

    if file_ext not in settings.ALLOWED_UPLOAD_TYPES:
        raise UnsupportedFileTypeError

    file_data = upload_file.file.read()

    if len(file_data) > settings.FILE_MAX_SIZE_KB:
        raise FileTooLargeError

    filename = await Storage.create(file_ext=file_ext, file_data=file_data)

    return Response(payload=filename)


@router.get("/storage/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    if not os.path.exists(f"data/{filename}"):
        raise NotFoundError

    if filename.endswith(".gltf"):
        return FileResponse(f"data/{filename}", media_type="application/octet-stream")
    return FileResponse(f"data/{filename}")
