"""created PAFunctionalCompetencyEvaluation table

Revision ID: 022f675c964a
Revises: 4b3d5346bf3a
Create Date: 2023-11-10 15:50:51.491255

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '022f675c964a'
down_revision = '4b3d5346bf3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pa_functional_competency_evaluations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('staff_account_id', sa.Integer(), nullable=True),
    sa.Column('evaluator_account_id', sa.Integer(), nullable=True),
    sa.Column('indicator_id', sa.Integer(), nullable=True),
    sa.Column('criterion_id', sa.Integer(), nullable=True),
    sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['criterion_id'], ['pa_functional_competency_indicators.id'], ),
    sa.ForeignKeyConstraint(['evaluator_account_id'], ['staff_account.id'], ),
    sa.ForeignKeyConstraint(['indicator_id'], ['pa_functional_competency_indicators.id'], ),
    sa.ForeignKeyConstraint(['staff_account_id'], ['staff_account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pa_functional_competency_evaluations')
    # ### end Alembic commands ###
