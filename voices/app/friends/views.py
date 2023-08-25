from voices.app.auth.views import UserView
from voices.app.core.protocol import BaseModel, PaginationView


class FriendListView(BaseModel):
    users: list[UserView]
    pagination: PaginationView
