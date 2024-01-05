"""added strategy ID field to KPI model


Revision ID: c463120dc991
Revises: e4c07caed126
Create Date: 2024-01-04 17:27:01.628780

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c463120dc991'
down_revision = 'e4c07caed126'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('kpis', schema=None) as batch_op:
        batch_op.add_column(sa.Column('strategy_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'strategies', ['strategy_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('kpis', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('strategy_id')

    # ### end Alembic commands ###
