"""Added is_quotaion column in ServiceCustomerAddress model

Revision ID: 44d5d5a3a6d0
Revises: 17111e553688
Create Date: 2024-12-04 11:44:09.540380

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '44d5d5a3a6d0'
down_revision = '17111e553688'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_addresses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_quotation', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_addresses', schema=None) as batch_op:
        batch_op.drop_column('is_quotation')
    # ### end Alembic commands ###
