"""added subdistrict models

Revision ID: fb7910f29cba
Revises: 6750b86e13a3
Create Date: 2018-01-24 08:17:11.918543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fb7910f29cba'
down_revision = '6750b86e13a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subdistricts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('district_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('subdistricts')
    # ### end Alembic commands ###
