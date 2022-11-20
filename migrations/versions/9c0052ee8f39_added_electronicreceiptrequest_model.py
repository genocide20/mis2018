"""Added ElectronicReceiptRequest model

Revision ID: 9c0052ee8f39
Revises: dbd518bf3d6b
Create Date: 2022-11-17 13:33:59.433000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c0052ee8f39'
down_revision = 'dbd518bf3d6b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('electronic_receipt_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=True),
    sa.Column('url_drive', sa.String(), nullable=True),
    sa.Column('created_at', sa.Date(), server_default=sa.text(u'now()'), nullable=True),
    sa.Column('staff_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['electronic_receipt_details.id'], ),
    sa.ForeignKeyConstraint(['staff_id'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'electronic_receipt_details', sa.Column('print_number', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'electronic_receipt_details', 'print_number')
    op.drop_table('electronic_receipt_requests')
    # ### end Alembic commands ###
