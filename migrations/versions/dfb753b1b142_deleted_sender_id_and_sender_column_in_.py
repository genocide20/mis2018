"""Deleted sender_id and sender column in ServicePayment moodel

Revision ID: dfb753b1b142
Revises: 5afbdd1abc3b
Create Date: 2025-02-07 15:10:08.013506

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dfb753b1b142'
down_revision = '5afbdd1abc3b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_payments', schema=None) as batch_op:
        batch_op.drop_constraint('service_payments_sender_id_fkey', type_='foreignkey')
        batch_op.drop_column('sender_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('service_payments_sender_id_fkey', 'service_customer_accounts', ['sender_id'], ['id'])
    # ### end Alembic commands ###
