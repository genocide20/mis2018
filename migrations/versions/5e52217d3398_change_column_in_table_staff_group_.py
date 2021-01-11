"""change column in table staff_group_assoc and staff_special_groups

Revision ID: 5e52217d3398
Revises: c54ac75b0be0
Create Date: 2021-01-11 16:24:03.465148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e52217d3398'
down_revision = 'c54ac75b0be0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'staff_group_assoc_staff_id_fkey', 'staff_group_assoc', type_='foreignkey')
    op.create_foreign_key(None, 'staff_group_assoc', 'staff_account', ['staff_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'staff_group_assoc', type_='foreignkey')
    op.create_foreign_key(u'staff_group_assoc_staff_id_fkey', 'staff_group_assoc', 'staff_personal_info', ['staff_id'], ['id'])
    # ### end Alembic commands ###
