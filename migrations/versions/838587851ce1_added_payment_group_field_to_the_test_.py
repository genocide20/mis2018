"""added payment group field to the test group model

Revision ID: 838587851ce1
Revises: 8ea8e029698a
Create Date: 2019-11-11 21:31:12.738501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '838587851ce1'
down_revision = '8ea8e029698a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comhealth_test_groups', sa.Column('payment_group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'comhealth_test_groups', 'comhealth_payment_group', ['payment_group_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comhealth_test_groups', type_='foreignkey')
    op.drop_column('comhealth_test_groups', 'payment_group_id')
    # ### end Alembic commands ###