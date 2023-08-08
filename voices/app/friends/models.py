import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, relationship

from voices.app.auth.models import User
from voices.models import BaseModel


class RelationshipType:
    FRIEND = "FRIEND"  # добавлен взаимно
    NOT_APPROVED = "NOT_APPROVED"  # ещё не одобрен
    FOLLOWER = "FOLLOWER"  # подписчик
    DECLINED = "DECLINED"  # отклонена


class Friend(BaseModel):
    __tablename__ = "users_friends"

    __table_args__ = (sa.UniqueConstraint("user_id", "initiative_id", name="_user_initiative_idx"),)

    user_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", foreign_keys="Friend.user_id")
    friend_id: Mapped[uuid.UUID] = sa.Column(sa.UUID, sa.ForeignKey("initiatives.id"), nullable=False)
    friend: Mapped[User] = relationship("User", foreign_keys="Friend.friend_id")
    relationship_type = sa.Column(sa.String(length=12), server_default=RelationshipType.NOT_APPROVED)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())
