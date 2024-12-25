"""Added customer_info_id and customer_info column in ServiceCustomerAccount model

Revision ID: 08bd12dae55c
Revises: 4565f5a29d53
Create Date: 2024-12-25 11:05:51.993118

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '08bd12dae55c'
down_revision = '4565f5a29d53'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_info_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_infos', ['customer_info_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_accounts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('customer_info_id')
    # ### end Alembic commands ###
