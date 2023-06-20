"""added a model for instructor roles in a course

Revision ID: 796e242a4e47
Revises: 007d2946c031
Create Date: 2022-12-06 09:38:36.121584

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '796e242a4e47'
down_revision = '007d2946c031'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('eduqa_course_instructor_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('eduqa_course_instructor_role_assoc',
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('instructor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['instructor_id'], ['eduqa_course_instructors.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['eduqa_course_instructor_roles.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('eduqa_course_instructor_role_assoc')
    op.drop_table('eduqa_course_instructor_roles')
    # ### end Alembic commands ###
