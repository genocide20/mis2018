"""Deleted result and result_id column in ServiceRequest model

Revision ID: a51e6adb193a
Revises: af179daa24b5
Create Date: 2025-01-01 21:55:38.570037

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a51e6adb193a'
down_revision = 'af179daa24b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_constraint('service_requests_result_id_fkey', type_='foreignkey')
        batch_op.drop_column('result_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('result_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('service_requests_result_id_fkey', 'service_results', ['result_id'], ['id'])
    # ### end Alembic commands ###
