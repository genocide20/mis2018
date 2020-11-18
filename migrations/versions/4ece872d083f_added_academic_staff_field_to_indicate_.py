"""added academic staff field to indicate a faculty or a researcher

Revision ID: 4ece872d083f
Revises: d04730f7b864
Create Date: 2020-11-08 18:21:18.664678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ece872d083f'
down_revision = 'd04730f7b864'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_personal_info', sa.Column('academic_staff', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_personal_info', 'academic_staff')
    # ### end Alembic commands ###