"""Added color column in ComplaintPriority model

Revision ID: 96558f6cfb44
Revises: a459e6222d7b
Create Date: 2024-06-04 13:38:38.696970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96558f6cfb44'
down_revision = 'a459e6222d7b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_priorities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('complaint_priorities', schema=None) as batch_op:
        batch_op.drop_column('color')

    # ### end Alembic commands ###
