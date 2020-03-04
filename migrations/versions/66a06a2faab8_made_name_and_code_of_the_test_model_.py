"""made name and code of the test model not nullable

Revision ID: 66a06a2faab8
Revises: ea82264d4a9f
Create Date: 2020-01-23 20:39:54.003824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66a06a2faab8'
down_revision = 'ea82264d4a9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('comhealth_tests', 'code',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
    op.alter_column('comhealth_tests', 'name',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('comhealth_tests', 'name',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)
    op.alter_column('comhealth_tests', 'code',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)
    # ### end Alembic commands ###
