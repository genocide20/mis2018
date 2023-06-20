"""added new columns (middle_level_approver_account_id and lower_level_approver_account_id) in staff_seminar_attends table

Revision ID: 3d8416fa1998
Revises: 91833d3e732b
Create Date: 2023-02-22 10:54:21.837410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d8416fa1998'
down_revision = '91833d3e732b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_seminar_attends', sa.Column('lower_level_approver_account_id', sa.Integer(), nullable=True))
    op.add_column('staff_seminar_attends', sa.Column('middle_level_approver_account_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'staff_seminar_attends', 'staff_account', ['lower_level_approver_account_id'], ['id'])
    op.create_foreign_key(None, 'staff_seminar_attends', 'staff_account', ['middle_level_approver_account_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'staff_seminar_attends', type_='foreignkey')
    op.drop_constraint(None, 'staff_seminar_attends', type_='foreignkey')
    op.drop_column('staff_seminar_attends', 'middle_level_approver_account_id')
    op.drop_column('staff_seminar_attends', 'lower_level_approver_account_id')
    # ### end Alembic commands ###
