"""Added pdf_file column in ComhealthReceipt model

Revision ID: 3b1999967872
Revises: 3c516012e1dd
Create Date: 2023-12-19 22:34:18.411055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b1999967872'
down_revision = '3c516012e1dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comhealth_test_receipts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pdf_file', sa.LargeBinary(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comhealth_test_receipts', schema=None) as batch_op:
        batch_op.drop_column('pdf_file')

    # ### end Alembic commands ###
