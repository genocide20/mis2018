"""created new table named staff_seminar_proposals to collect details of seminar proposal

Revision ID: c62da24df658
Revises: 3d8416fa1998
Create Date: 2023-02-27 16:21:59.202825

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c62da24df658'
down_revision = '3d8416fa1998'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staff_seminar_proposals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('seminar_attend_id', sa.Integer(), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_approved', sa.Boolean(), nullable=True),
    sa.Column('approval_comment', sa.String(), nullable=True),
    sa.Column('proposer_account_id', sa.Integer(), nullable=True),
    sa.Column('previous_proposal_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['proposer_account_id'], ['staff_account.id'], ),
    sa.ForeignKeyConstraint(['seminar_attend_id'], ['staff_seminar_attends.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('staff_seminar_proposals')
    # ### end Alembic commands ###
