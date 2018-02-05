"""replaced sample produce with grown produce.

Revision ID: 8a1efca06e2a
Revises: aa267a6574c0
Create Date: 2018-02-06 02:04:10.624468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a1efca06e2a'
down_revision = 'aa267a6574c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('food_samples', sa.Column('grown_produce_id', sa.Integer(), nullable=True))
    op.drop_constraint(u'food_samples_produce_id_fkey', 'food_samples', type_='foreignkey')
    op.create_foreign_key(None, 'food_samples', 'food_grown_produces', ['grown_produce_id'], ['id'])
    op.drop_column('food_samples', 'produce_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('food_samples', sa.Column('produce_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'food_samples', type_='foreignkey')
    op.create_foreign_key(u'food_samples_produce_id_fkey', 'food_samples', 'food_produces', ['produce_id'], ['id'])
    op.drop_column('food_samples', 'grown_produce_id')
    # ### end Alembic commands ###
