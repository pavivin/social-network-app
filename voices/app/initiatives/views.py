import uuid
from datetime import datetime

from voices.app.core.protocol import BaseModel, GeometryPoint, PaginationView

from .models import Initiative


class UserView(BaseModel):
    first_name: str = "unknown"
    last_name: str = "user"
    image_url: str | None


class InitiativeView(BaseModel):
    id: str | uuid.UUID
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
    pagination: PaginationView


class CommentView(BaseModel):
    id: uuid.UUID
    created_at: str | datetime
    user: UserView
    main_text: str


class CommentReplyView(CommentView):
    replies: list[CommentView] = []


class CommentListView(BaseModel):
    comments: list[CommentReplyView]
    pagination: PaginationView


class CommentRequestView(BaseModel):
    main_text: str
