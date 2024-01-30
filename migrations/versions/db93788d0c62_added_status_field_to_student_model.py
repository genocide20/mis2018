"""added status field to student model

Revision ID: db93788d0c62
Revises: c2881c7ddefa
Create Date: 2023-12-12 10:30:18.020931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db93788d0c62'
down_revision = 'c2881c7ddefa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=16), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_students', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
