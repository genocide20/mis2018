"""Removed cost center and internal order in ElectronicReceiptItem model

Revision ID: 9a3e93353177
Revises: 762223d6ab34
Create Date: 2022-11-20 13:20:47.547000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a3e93353177'
down_revision = '762223d6ab34'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('electronic_receipt_items', 'internal_order')
    op.drop_column('electronic_receipt_items', 'cost_center')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('electronic_receipt_items', sa.Column('cost_center', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('electronic_receipt_items', sa.Column('internal_order', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
