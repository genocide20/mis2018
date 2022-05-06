"""added new column named is_count_in_mins in OtCompensationRate table

Revision ID: 6b3441ec8619
Revises: 8d60980b4a3a
Create Date: 2022-05-06 16:08:03.099293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b3441ec8619'
down_revision = '8d60980b4a3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ot_compensation_rate', sa.Column('is_count_in_mins', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ot_compensation_rate', 'is_count_in_mins')
    # ### end Alembic commands ###
