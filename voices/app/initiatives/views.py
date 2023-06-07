import uuid
from datetime import datetime

from voices.protocol import BaseModel, GeometryPoint

from .models import Initiative


class UserView(BaseModel):
    first_name: str
    last_name: str
    image_url: str | None


class InitiativeView(BaseModel):
    user: UserView
    city: str
    images: list | dict | None
    category: Initiative.Category
    location: GeometryPoint | None
    title: str
    main_text: str
    likes_count: int
    comments_count: int
    reposts_count: int


class InitiativeListView(BaseModel):
    feed: list[InitiativeView]


class CommentView(BaseModel):
    id: uuid.UUID
    created_at: str | datetime
    user: UserView
    main_text: str


class CommentReplyView(CommentView):
    replies: list[CommentView] = []


class CommentListView(BaseModel):
    comments: list[CommentReplyView]


class CommentRequestView(BaseModel):
    main_text: str
