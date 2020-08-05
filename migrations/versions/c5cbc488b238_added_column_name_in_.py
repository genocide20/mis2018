"""added column name in StaffWorkFromHomeCheckedJob

Revision ID: c5cbc488b238
Revises: b1847e82f0da
Create Date: 2020-05-26 21:20:58.039032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5cbc488b238'
down_revision = 'b1847e82f0da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_work_from_home_checked_job', sa.Column('approver_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'staff_work_from_home_checked_job', 'staff_account', ['approver_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'staff_work_from_home_checked_job', type_='foreignkey')
    op.drop_column('staff_work_from_home_checked_job', 'approver_id')
    # ### end Alembic commands ###