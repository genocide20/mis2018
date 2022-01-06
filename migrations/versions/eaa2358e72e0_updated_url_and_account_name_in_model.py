"""Updated url and account name in Model

Revision ID: eaa2358e72e0
Revises: 128b45ff9548
Create Date: 2021-12-03 15:31:20.652000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eaa2358e72e0'
down_revision = '128b45ff9548'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tracker_accounts', sa.Column('url', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tracker_accounts', 'url')
    # ### end Alembic commands ###