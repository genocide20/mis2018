"""Added taxpayer_identification_no column in ServiceCustomerInfo model

Revision ID: 36cdbb58e0ac
Revises: 9f9b12455a0a
Create Date: 2024-07-15 11:29:28.523610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36cdbb58e0ac'
down_revision = '9f9b12455a0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('taxpayer_identification_no', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_column('taxpayer_identification_no')

    # ### end Alembic commands ###
