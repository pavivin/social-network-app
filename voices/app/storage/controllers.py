import os
from io import BytesIO
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

from voices.app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from voices.app.core.protocol import Response
from voices.config import settings


class Storage:
    @classmethod
    def compress_jpeg(cls, file_data: bytes, filename: str):
        foo = Image.open(BytesIO(file_data))

        foo = foo.resize((foo.size), Image.LANCZOS)

        foo.save(f"data/{filename}", optimize=True, quality=80)

    @classmethod
    def get_filename(cls, file_ext: str):
        return f"{uuid4().hex}.{file_ext}"

    @classmethod
    async def create(cls, filename: str, file_ext: str, file_data: bytes):
        if file_ext == "jpg":
            cls.compress_jpeg(file_data=file_data, filename=filename)
        else:
            async with aiofiles.open(f"data/{filename}", mode="wb") as f:
                await f.write(file_data)


router = APIRouter()


# TODO: to webp
@router.post("/storage", response_model=Response)
async def add_file(upload_file: UploadFile):
    file_ext = upload_file.filename.split(".")[-1].lower()

    if file_ext not in settings.ALLOWED_UPLOAD_TYPES:
        raise UnsupportedFileTypeError

    file_data = upload_file.file.read()

    if len(file_data) > settings.FILE_MAX_SIZE_KB:
        raise FileTooLargeError

    filename = Storage.get_filename(file_ext)

    await Storage.create(filename=filename, file_ext=file_ext, file_data=file_data)

    return Response(payload=filename)


@router.get("/storage/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    if not os.path.exists(f"data/{filename}"):
        raise NotFoundError

    return FileResponse(f"data/{filename}")
