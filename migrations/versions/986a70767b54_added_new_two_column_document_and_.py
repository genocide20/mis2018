"""added new two column document and reason required in table StaffLeaveType

Revision ID: 986a70767b54
Revises: fabbfe64f164
Create Date: 2020-08-25 10:24:09.708927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '986a70767b54'
down_revision = 'fabbfe64f164'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('staff_leave_types', sa.Column('document_required', sa.Boolean(), nullable=True))
    op.add_column('staff_leave_types', sa.Column('reason_required', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('staff_leave_types', 'reason_required')
    op.drop_column('staff_leave_types', 'document_required')
    # ### end Alembic commands ###
