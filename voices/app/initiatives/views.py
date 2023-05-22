import uuid

from voices.protocol import BaseModel, GeometryPoint

from .models import Initiative


class UserView(BaseModel):
    first_name: str
    last_name: str


class InitiativeView(BaseModel):
    user_id: uuid.UUID
    city: str
    images: list[dict] | None
    category: Initiative.Category
    location: GeometryPoint | None
    title: str
    main_text: str


class InitiativeListView(BaseModel):
    feed: list[InitiativeView]
