"""added is_success result_detail learing_type_id approver_comment columns in IDPItem table

Revision ID: f0528b0dd09c
Revises: fccc52d3cc64
Create Date: 2024-01-09 14:33:37.274614

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0528b0dd09c'
down_revision = 'fccc52d3cc64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('idp_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_success', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('result_detail', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('learning_type_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('approver_comment', sa.String(), nullable=True))
        batch_op.create_foreign_key(None, 'idp_learning_type', ['learning_type_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('idp_items', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('approver_comment')
        batch_op.drop_column('learning_type_id')
        batch_op.drop_column('result_detail')
        batch_op.drop_column('is_success')

    # ### end Alembic commands ###