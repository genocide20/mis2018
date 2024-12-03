"""Added adder_id and adder column in ServiceCustomerContact model and added customer_id and customer coumn in ServiceCustomerAddress model

Revision ID: 757fe69ca056
Revises: 70fd5646b5e2
Create Date: 2024-12-03 12:07:41.264442

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '757fe69ca056'
down_revision = '70fd5646b5e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_addresses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_accounts', ['customer_id'], ['id'])

    with op.batch_alter_table('service_customer_contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('adder_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_accounts', ['adder_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_contacts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('adder_id')

    with op.batch_alter_table('service_customer_addresses', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('customer_id')
    # ### end Alembic commands ###
