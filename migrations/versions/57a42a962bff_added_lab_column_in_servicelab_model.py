"""Added lab column in ServiceLab model

Revision ID: 57a42a962bff
Revises: 1d9adfc41fb1
Create Date: 2024-11-07 14:02:28.869173

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '57a42a962bff'
down_revision = '1d9adfc41fb1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_labs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lab', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_labs', schema=None) as batch_op:
        batch_op.drop_column('lab')
    # ### end Alembic commands ###
