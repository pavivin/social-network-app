from blacksheep import json
from blacksheep.server.controllers import Controller, post

from vizme.db.connection import Transaction
from vizme.protocol import Response

from .models import Cats


class CatsController(Controller):
    @post("/api/cats")
    async def index(self) -> Response:
        async with Transaction():
            # TODO: tests for check on same transaction
            await Cats.create(name="ContextVar")
            await Cats.update(name="Transaction")

        # TODO: rewrite to something more readable
        return json(Response().dict())
