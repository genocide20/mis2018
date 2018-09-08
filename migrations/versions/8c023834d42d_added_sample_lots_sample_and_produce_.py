"""added sample lots, sample and produce models

Revision ID: 8c023834d42d
Revises: 9efd490c4834
Create Date: 2018-01-25 10:17:36.105818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c023834d42d'
down_revision = '9efd490c4834'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('food_produces',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('food_sample_lots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('collected_at', sa.DateTime(), nullable=True),
    sa.Column('registered_at', sa.DateTime(), nullable=True),
    sa.Column('farm_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['farm_id'], ['food_farms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('food_samples',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lot_id', sa.Integer(), nullable=True),
    sa.Column('produce_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lot_id'], ['food_sample_lots.id'], ),
    sa.ForeignKeyConstraint(['produce_id'], ['food_produces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('food_samples')
    op.drop_table('food_sample_lots')
    op.drop_table('food_produces')
    # ### end Alembic commands ###
