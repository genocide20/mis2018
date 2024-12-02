"""added sap id field

Revision ID: 890b56564a68
Revises: a92ba5f8e1cd
Create Date: 2024-03-25 14:57:54.399478

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '890b56564a68'
down_revision = 'a92ba5f8e1cd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('staff_personal_info', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sap_id', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('staff_personal_info', schema=None) as batch_op:
        batch_op.drop_column('sap_id')

    # ### end Alembic commands ###
