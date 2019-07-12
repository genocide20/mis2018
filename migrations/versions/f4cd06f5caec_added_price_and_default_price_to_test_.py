"""added price and default price to test item and test

Revision ID: f4cd06f5caec
Revises: b5a87a83307f
Create Date: 2019-03-20 03:26:28.048074

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4cd06f5caec'
down_revision = 'b5a87a83307f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comhealth_test_group_assoc')
    op.drop_table('comhealth_test_profile_assoc')
    op.add_column('comhealth_test_groups', sa.Column('age_max', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_groups', sa.Column('age_min', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_groups', sa.Column('gender', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_items', sa.Column('group_id', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_items', sa.Column('price', sa.Numeric(), nullable=True))
    op.add_column('comhealth_test_items', sa.Column('profile_id', sa.Integer(), nullable=True))
    op.drop_constraint(u'comhealth_test_items_record_id_fkey', 'comhealth_test_items', type_='foreignkey')
    op.create_foreign_key(None, 'comhealth_test_items', 'comhealth_test_groups', ['group_id'], ['id'])
    op.create_foreign_key(None, 'comhealth_test_items', 'comhealth_test_profiles', ['profile_id'], ['id'])
    op.drop_column('comhealth_test_items', 'record_id')
    op.add_column('comhealth_test_profiles', sa.Column('age_max', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_profiles', sa.Column('age_min', sa.Integer(), nullable=True))
    op.add_column('comhealth_test_profiles', sa.Column('gender', sa.Integer(), nullable=True))
    op.add_column('comhealth_tests', sa.Column('default_price', sa.Numeric(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comhealth_tests', 'default_price')
    op.drop_column('comhealth_test_profiles', 'gender')
    op.drop_column('comhealth_test_profiles', 'age_min')
    op.drop_column('comhealth_test_profiles', 'age_max')
    op.add_column('comhealth_test_items', sa.Column('record_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'comhealth_test_items', type_='foreignkey')
    op.drop_constraint(None, 'comhealth_test_items', type_='foreignkey')
    op.create_foreign_key(u'comhealth_test_items_record_id_fkey', 'comhealth_test_items', 'comhealth_test_records', ['record_id'], ['id'])
    op.drop_column('comhealth_test_items', 'profile_id')
    op.drop_column('comhealth_test_items', 'price')
    op.drop_column('comhealth_test_items', 'group_id')
    op.drop_column('comhealth_test_groups', 'gender')
    op.drop_column('comhealth_test_groups', 'age_min')
    op.drop_column('comhealth_test_groups', 'age_max')
    op.create_table('comhealth_test_profile_assoc',
    sa.Column('test_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('profile_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['profile_id'], [u'comhealth_test_profiles.id'], name=u'comhealth_test_profile_assoc_profile_id_fkey'),
    sa.ForeignKeyConstraint(['test_id'], [u'comhealth_tests.id'], name=u'comhealth_test_profile_assoc_test_id_fkey'),
    sa.PrimaryKeyConstraint('test_id', 'profile_id', name=u'comhealth_test_profile_assoc_pkey')
    )
    op.create_table('comhealth_test_group_assoc',
    sa.Column('test_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('group_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['group_id'], [u'comhealth_test_groups.id'], name=u'comhealth_test_group_assoc_group_id_fkey'),
    sa.ForeignKeyConstraint(['test_id'], [u'comhealth_tests.id'], name=u'comhealth_test_group_assoc_test_id_fkey'),
    sa.PrimaryKeyConstraint('test_id', 'group_id', name=u'comhealth_test_group_assoc_pkey')
    )
    # ### end Alembic commands ###
