"""added data tag model

Revision ID: f6f0f617705a
Revises: c0300c9ba983
Create Date: 2022-12-14 13:56:21.870415

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6f0f617705a'
down_revision = 'c0300c9ba983'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('db_datatags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tag', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tag')
    )
    op.create_table('db_dataset_tag_assoc',
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['db_datasets.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['db_datatags.id'], ),
    sa.PrimaryKeyConstraint('dataset_id', 'tag_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('db_dataset_tag_assoc')
    op.drop_table('db_datatags')
    # ### end Alembic commands ###