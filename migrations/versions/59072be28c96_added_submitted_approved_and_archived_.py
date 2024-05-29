"""added submitted, approved and archived datetime fields

Revision ID: 59072be28c96
Revises: a6eea0015f83
Create Date: 2024-05-29 15:37:24.913013

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59072be28c96'
down_revision = 'a6eea0015f83'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_submitted', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('report_approved_datetime', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('archived_datetime', sa.DateTime(timezone=True), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('eduqa_courses', schema=None) as batch_op:
        batch_op.drop_column('archived_datetime')
        batch_op.drop_column('report_approved_datetime')
        batch_op.drop_column('report_submitted')

    # ### end Alembic commands ###
