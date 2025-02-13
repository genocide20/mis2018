"""Deleted appointment_id and appointment column in ServiceRequest model

Revision ID: 32783ba86182
Revises: 8a9d52938a74
Create Date: 2025-01-30 08:51:44.846717

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '32783ba86182'
down_revision = '8a9d52938a74'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_constraint('service_requests_appointment_id_fkey', type_='foreignkey')
        batch_op.drop_column('appointment_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('appointment_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('service_requests_appointment_id_fkey', 'service_sample_appointments', ['appointment_id'], ['id'])
    # ### end Alembic commands ###
