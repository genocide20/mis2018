"""added detail column in IDPRequest table

Revision ID: bf37d866b1b0
Revises: bfdce929953c
Create Date: 2024-01-10 16:27:03.801009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf37d866b1b0'
down_revision = 'bfdce929953c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('idp_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('detail', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('idp_requests', schema=None) as batch_op:
        batch_op.drop_column('detail')

    # ### end Alembic commands ###
