"""added is_focused field

Revision ID: 6fc90d663e58
Revises: b42005a6175a
Create Date: 2024-03-01 17:13:22.965594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fc90d663e58'
down_revision = 'b42005a6175a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_evaluation_indicators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_focused', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_evaluation_indicators', schema=None) as batch_op:
        batch_op.drop_column('is_focused')

    # ### end Alembic commands ###
