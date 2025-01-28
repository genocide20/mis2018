"""Added approver_id and approver column in ServiceQuotation model

Revision ID: e83c6db9ab41
Revises: 15e26ccae705
Create Date: 2025-01-28 09:53:10.318789

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e83c6db9ab41'
down_revision = '15e26ccae705'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('approver_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'service_customer_accounts', ['approver_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_quotations', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('approver_id')
    # ### end Alembic commands ###
