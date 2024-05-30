"""Deleted validated_datetime column in ServiceCustomerInfo model

Revision ID: 59f6aeebbc59
Revises: 719f00de54e5
Create Date: 2024-05-28 14:42:12.726005

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '59f6aeebbc59'
down_revision = '719f00de54e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_column('validated_datetime')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validated_datetime', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
