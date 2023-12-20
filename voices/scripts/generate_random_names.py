import asyncio

from voices.app.auth.models import User
from voices.db.connection import Transaction
from faker import Faker

import random

import requests

faker_ru = Faker("ru_RU")


def get_random_name():
    sex = random.choice(["male", "female"])

    first_name = getattr(faker_ru, f"first_name_{sex}")()
    last_name = getattr(faker_ru, f"last_name_{sex}")()

    response = requests.get(f"https://randomuser.me/api/?gender={sex}")
    answer = response.json()
    image_url = answer["results"][0]["picture"]["medium"]

    return first_name, last_name, image_url


async def handle():
    async with Transaction() as tr:
        db_users = await User.get_all()

        for user in db_users:
            last_name, first_name, image_url = get_random_name()

            user.first_name = first_name
            user.last_name = last_name
            user.image_url = image_url

            await tr.session.commit()


asyncio.run(handle())
