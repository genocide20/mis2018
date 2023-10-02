"""removed meeting poll participant model

Revision ID: d6ead85237db
Revises: 11db55c9b648
Create Date: 2023-09-14 11:21:29.251721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6ead85237db'
down_revision = '11db55c9b648'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_poll_participant_assoc',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=True),
    sa.Column('poll_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['poll_id'], ['meeting_polls.id'], ),
    sa.ForeignKeyConstraint(['staff_id'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('meeting_poll_item_participants',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('poll_participant_id', sa.Integer(), nullable=True),
    sa.Column('item_poll_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_poll_id'], ['meeting_poll_items.id'], ),
    sa.ForeignKeyConstraint(['poll_participant_id'], ['meeting_poll_participant_assoc.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('meeting_poll_participants')
    op.drop_table('meeting_item_assoc')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_item_assoc',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('poll_item_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['poll_item_id'], ['meeting_poll_items.id'], name='meeting_item_assoc_poll_item_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['staff_account.id'], name='meeting_item_assoc_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='meeting_item_assoc_pkey')
    )
    op.create_table('meeting_poll_participants',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('participant_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('poll_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['participant_id'], ['staff_account.id'], name='meeting_poll_participants_participant_id_fkey'),
    sa.ForeignKeyConstraint(['poll_id'], ['meeting_polls.id'], name='meeting_poll_participants_poll_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='meeting_poll_participants_pkey')
    )
    op.drop_table('meeting_poll_item_participants')
    op.drop_table('meeting_poll_participant_assoc')
    # ### end Alembic commands ###
