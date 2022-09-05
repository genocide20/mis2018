"""deleted StaffPosition table

Revision ID: 7039019381ca
Revises: 51604e22092b
Create Date: 2022-08-05 16:18:20.158830

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7039019381ca'
down_revision = '51604e22092b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('staff_positions')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staff_positions',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('position', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'staff_positions_pkey')
    )
    # ### end Alembic commands ###
