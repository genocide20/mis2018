"""added suggestion field

Revision ID: e2fcbac03fb4
Revises: 3e414d100b03
Create Date: 2023-12-20 07:42:06.287241

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2fcbac03fb4'
down_revision = '3e414d100b03'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_instructor_evaluations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('suggestion', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_instructor_evaluations', schema=None) as batch_op:
        batch_op.drop_column('suggestion')

    # ### end Alembic commands ###
