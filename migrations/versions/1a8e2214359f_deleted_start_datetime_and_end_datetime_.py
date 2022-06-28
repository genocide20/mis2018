"""deleted start_datetime and end_datetime columns of ot_compensation_rate table

Revision ID: 1a8e2214359f
Revises: 84f06a175104
Create Date: 2021-11-04 10:05:04.916784

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a8e2214359f'
down_revision = '84f06a175104'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ot_compensation_rate', 'start_datetime')
    op.drop_column('ot_compensation_rate', 'end_datetime')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ot_compensation_rate', sa.Column('end_datetime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('ot_compensation_rate', sa.Column('start_datetime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
