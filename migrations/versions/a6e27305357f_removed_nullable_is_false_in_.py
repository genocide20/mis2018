"""Removed nullable is false in procurement no column in ProcurementDetail model

Revision ID: a6e27305357f
Revises: 9b4eba0ef668
Create Date: 2022-09-28 14:12:21.722000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6e27305357f'
down_revision = '9b4eba0ef668'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(u'procurement_details', 'procurement_no',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(u'procurement_details', 'procurement_no',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
