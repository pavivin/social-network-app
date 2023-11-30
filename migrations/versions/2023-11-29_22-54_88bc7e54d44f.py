"""address

Revision ID: 88bc7e54d44f
Revises: 3a9ca236cbae
Create Date: 2023-11-29 22:54:00.336702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88bc7e54d44f'
down_revision = '3a9ca236cbae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('initiatives', sa.Column('address', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('initiatives', 'address')
    # ### end Alembic commands ###
