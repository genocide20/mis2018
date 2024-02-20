"""Added complaint_record_procurement_assoc Table and procurements column in ComplaintRecord

Revision ID: 46cd72a9d261
Revises: 24ab4ea2e161
Create Date: 2024-02-20 15:10:37.135612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '46cd72a9d261'
down_revision = '24ab4ea2e161'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('complaint_record_procurement_assoc',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('procurement_id', sa.Integer(), nullable=True),
    sa.Column('record_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['procurement_id'], ['procurement_details.id'], ),
    sa.ForeignKeyConstraint(['record_id'], ['complaint_records.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('meeting_group_assoc')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_group_assoc',
    sa.Column('group_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('poll_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['staff_group_details.id'], name='meeting_group_assoc_group_id_fkey'),
    sa.ForeignKeyConstraint(['poll_id'], ['meeting_polls.id'], name='meeting_group_assoc_poll_id_fkey')
    )
    op.drop_table('complaint_record_procurement_assoc')
    # ### end Alembic commands ###
