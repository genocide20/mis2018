"""Added validated_datetime column in ServiceCustomerInfo model

Revision ID: 4f948fcf1f02
Revises: 535335753625
Create Date: 2024-05-08 16:23:53.147981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f948fcf1f02'
down_revision = '535335753625'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validated_datetime', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_column('validated_datetime')

    # ### end Alembic commands ###
