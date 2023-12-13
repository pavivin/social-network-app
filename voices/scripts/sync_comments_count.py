import asyncio
from voices.app.initiatives.models import Comment, Initiative

from voices.db.connection import Transaction


async def handle():
    async with Transaction() as tr:
        initiative_list = await Initiative.get_all()
        for initiative in initiative_list:
            comments_count: int = await Comment.get_comments(initiative_id=initiative.id, is_total=True)
            initiative.comments_count = comments_count
            await tr.session.commit()


asyncio.run(handle())
