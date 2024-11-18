"""Added ship_type column in ServiceSampleAppointment model

Revision ID: 71398a513637
Revises: cfc0e49b1a4c
Create Date: 2024-11-15 16:57:43.134776

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '71398a513637'
down_revision = 'cfc0e49b1a4c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_sample_appointments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ship_type', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_sample_appointments', schema=None) as batch_op:
        batch_op.drop_column('ship_type')
    # ### end Alembic commands ###
