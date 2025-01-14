"""Added customer_id and customer column in ServiceResult model

Revision ID: d4b868000e10
Revises: 6eae28f414a8
Create Date: 2025-01-14 13:31:08.502375

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4b868000e10'
down_revision = '6eae28f414a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('customer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_accounts', ['customer_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_results', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('customer_id')
    # ### end Alembic commands ###
