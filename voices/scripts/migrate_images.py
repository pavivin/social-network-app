import asyncio
import io
import time

# import aiofiles
import requests
from PIL import Image
from uuid_extensions import uuid7

from voices.app.auth.models import User
from voices.app.initiatives.models import Initiative
from voices.app.storage.s3 import S3Service
from voices.config import settings
from voices.db.connection import Transaction
import webp

# uuid7str


async def migrate_images(image_list: list[User], tr: Transaction):
    for model in image_list:
        image = model.image_url
        if image.endswith("064e74c0198f7159800002e35c77df4a.jpg"):
            model.image_url = (
                "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b.webp"
            )  # default image
            continue

        if image.startswith("https://storage.yandexcloud.net/my-city"):
            continue

        file_data = requests.get(image).content
        if image.startswith("https://voices-city.ru/"):
            filename = image.split("/")[-1].split(".")[-2]
        else:
            filename = uuid7(as_type="hex")

        file_ext = image.split(".")[-1].lower()
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

            model.image_url = f"https://storage.yandexcloud.net/my-city/{max_image_path}"
        else:
            full_path = f"{filename}.{file_ext}"
            await S3Service.put_object(img_name=full_path, file=file_data)

        await tr.session.commit()


async def migrate_list_images(image_list: list[Initiative], tr: Transaction):
    for model in image_list:
        images: list[str] = model.images
        new_images = []
        is_continue = False
        for image in images:
            if image.endswith("064e74c0198f7159800002e35c77df4a.jpg"):
                model.image_url = (
                    "https://storage.yandexcloud.net/my-city/06563fe7f2a779b280000970701fa57b.webp"
                )  # default image
                continue

            if image.startswith("https://storage.yandexcloud.net/my-city"):
                is_continue = True
                continue

            file_data = requests.get(image).content
            if image.startswith("https://voices-city.ru/"):
                filename = image.split("/")[-1].split(".")[-2]
            else:
                filename = uuid7(as_type="hex")

            file_ext = image.split(".")[-1].lower()
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

                new_images.append(f"https://storage.yandexcloud.net/my-city/{max_image_path}")
            else:
                full_path = f"{filename}.{file_ext}"
                await S3Service.put_object(img_name=full_path, file=file_data)

                new_images.append(full_path)

        if not is_continue:
            model.images = new_images
            await tr.session.commit()
        time.sleep(1)


async def handle():
    await S3Service.get_s3_client()
    async with Transaction() as tr:
        # model_list = await User.get_all()
        # await migrate_images(model_list, tr=tr)

        model_list = await Initiative.get_all()
        await migrate_list_images(model_list, tr=tr)


asyncio.run(handle())
