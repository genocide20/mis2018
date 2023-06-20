"""added new column named org_structure_id in staff_head_positions table

Revision ID: c325fdf7a6a8
Revises: c32f4bda86b3
Create Date: 2023-05-11 10:22:57.573032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c325fdf7a6a8'
down_revision = 'c32f4bda86b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_head_positions', sa.Column('org_structure_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'staff_head_positions', 'org_structure', ['org_structure_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'staff_head_positions', type_='foreignkey')
    op.drop_column('staff_head_positions', 'org_structure_id')
    # ### end Alembic commands ###
