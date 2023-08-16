"""added PAItemCategory model

Revision ID: 7782b87d0b75
Revises: 510402035859
Create Date: 2023-06-20 03:16:52.554091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7782b87d0b75'
down_revision = '510402035859'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pa_item_categories',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pa_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('pa_items_category_id_fkey',
                                    'pa_item_categories', ['category_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_items', schema=None) as batch_op:
        batch_op.drop_constraint('pa_items_category_id_fkey', type_='foreignkey')
        batch_op.drop_column('category_id')

    op.drop_table('pa_item_categories')
    # ### end Alembic commands ###
