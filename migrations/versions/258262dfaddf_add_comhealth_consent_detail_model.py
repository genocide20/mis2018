"""add comhealth consent detail model

Revision ID: 258262dfaddf
Revises: 536667d368be
Create Date: 2022-06-26 21:01:10.762000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '258262dfaddf'
down_revision = '536667d368be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comhealth_consent_details',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('details', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text(u'now()'), nullable=True),
    sa.Column('creator', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['creator'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comhealth_consent_details')
    # ### end Alembic commands ###