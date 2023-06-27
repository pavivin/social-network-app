"""comments

Revision ID: 900da1a8ef74
Revises: 09a21554deff
Create Date: 2023-06-27 21:13:06.596524

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "900da1a8ef74"
down_revision = "09a21554deff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "comments",
        sa.Column("main_text", sa.String(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("initiative_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["initiative_id"],
            ["initiatives.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["comments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.alter_column("initiatives", "category", existing_type=sa.VARCHAR(length=15), nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("initiatives", "category", existing_type=sa.VARCHAR(length=15), nullable=False)
    op.drop_table("comments")
    # ### end Alembic commands ###
