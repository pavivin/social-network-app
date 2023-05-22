"""test

Revision ID: aebd719bf2f3
Revises: d25475720458
Create Date: 2023-05-19 14:51:11.592842

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "aebd719bf2f3"
down_revision = "d25475720458"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE EXTENSION postgis")
    op.create_table(
        "initiatives",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("city", sa.String(length=35), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category", sa.String(length=15), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("idx_initiatives_location", "initiatives", ["location"], unique=False, postgresql_using="gist")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_initiatives_location", table_name="initiatives", postgresql_using="gist")
    op.drop_table("initiatives")
    # ### end Alembic commands ###
