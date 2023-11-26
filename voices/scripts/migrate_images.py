import asyncio
import io

# import aiofiles
import requests
from PIL import Image
from uuid_extensions import uuid7

from voices.app.auth.models import User
from voices.app.storage.s3 import S3Service
from voices.config import Settings
from voices.db.connection import Transaction

# uuid7str


async def handle():
    async with Transaction():
        db_users = await User.get_all_images()
        for image in db_users:
            file_data = requests.get(image).content
            if image.startswith("https://voices-city.ru/"):
                filename = image.split("/")[-1]
            else:
                uuid7()

            filename = uuid7().hex
            file_ext = image.split(".")[-1].lower()
            if file_ext in Settings.ALLOWED_PHOTO_TYPES:
                webp_image = Image.open(io.BytesIO(file_data))
                webp_image.save(f"data/{filename}.webp", format="Webp")
                mini_image = webp_image.resize(size=(100, 100))
                mini_image.save(f"data/{filename}-100x100.webp", format="Webp")
                full_path = f"{filename}.webp"
            else:
                full_path = f"{filename}.{file_ext}"
                S3Service.put_object()
            full_path


asyncio.run(handle())
