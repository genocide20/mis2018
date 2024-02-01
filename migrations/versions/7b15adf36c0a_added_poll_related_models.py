"""added poll-related models

Revision ID: 7b15adf36c0a
Revises: ea7c4d5b5102
Create Date: 2023-09-06 17:10:07.100560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b15adf36c0a'
down_revision = 'ea7c4d5b5102'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_polls',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('poll_name', sa.String(), nullable=False),
    sa.Column('start_vote', sa.DateTime(timezone=True), nullable=False),
    sa.Column('close_vote', sa.DateTime(timezone=True), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('meeting_poll_items',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('date_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('poll_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['poll_id'], ['meeting_polls.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('meeting_item_assoc',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('poll_item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['poll_item_id'], ['meeting_poll_items.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('meeting_item_assoc')
    op.drop_table('meeting_poll_items')
    op.drop_table('meeting_polls')
    # ### end Alembic commands ###
