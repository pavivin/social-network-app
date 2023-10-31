import io
import os

import aiofiles
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
from voices.config import settings


class Storage:
    @classmethod
    async def create(cls, file_ext: str, file_data: bytes):
        filename = uuid7().hex
        if file_ext in settings.ALLOWED_PHOTO_TYPES:
            webp_image = Image.open(io.BytesIO(file_data))
            webp_image.save(f"data/{filename}-max.webp", format="Webp")
            mini_image = webp_image.resize(size=(100, 100))
            mini_image.save(f"data/{filename}-100x100.webp", format="Webp")
            return f"{filename}.webp"

        full_path = f"{filename}.{file_ext}"
        async with aiofiles.open(f"data/{full_path}", mode="wb") as f:
            await f.write(file_data)
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
