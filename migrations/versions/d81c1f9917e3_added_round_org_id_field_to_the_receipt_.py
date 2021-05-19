"""added round org ID field to the receipt model

Revision ID: d81c1f9917e3
Revises: 19fe3913ec38
Create Date: 2021-05-19 22:05:39.095598

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd81c1f9917e3'
down_revision = '19fe3913ec38'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('doc_receive_records', sa.Column('round_org_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'doc_receive_records', 'doc_round_orgs', ['round_org_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'doc_receive_records', type_='foreignkey')
    op.drop_column('doc_receive_records', 'round_org_id')
    # ### end Alembic commands ###
