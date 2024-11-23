"""Deleted organization_type_id and organization_type column in ServiceCustomerInfo model

Revision ID: 30856cc96849
Revises: bdf495c9b04f
Create Date: 2024-11-14 09:43:37.628042

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '30856cc96849'
down_revision = 'bdf495c9b04f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.drop_constraint('service_customer_infos_organization_type_id_fkey', type_='foreignkey')
        batch_op.drop_column('organization_type_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_customer_infos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('organization_type_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('service_customer_infos_organization_type_id_fkey', 'service_organization_types', ['organization_type_id'], ['id'])
    # ### end Alembic commands ###
