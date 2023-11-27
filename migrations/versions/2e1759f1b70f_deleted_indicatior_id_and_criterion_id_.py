"""deleted indicatior_id and criterion_id column in PAFunctionalCompetencyEvaluation table

Revision ID: 2e1759f1b70f
Revises: 32cda485c53a
Create Date: 2023-11-22 14:20:58.163682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e1759f1b70f'
down_revision = '32cda485c53a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_evaluations', schema=None) as batch_op:
        batch_op.drop_constraint('pa_functional_competency_evaluations_indicator_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('pa_functional_competency_evaluations_criterion_id_fkey', type_='foreignkey')
        batch_op.drop_column('criterion_id')
        batch_op.drop_column('indicator_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pa_functional_competency_evaluations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('indicator_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('criterion_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('pa_functional_competency_evaluations_criterion_id_fkey', 'pa_functional_competency_criteria', ['criterion_id'], ['id'])
        batch_op.create_foreign_key('pa_functional_competency_evaluations_indicator_id_fkey', 'pa_functional_competency_indicators', ['indicator_id'], ['id'])

    # ### end Alembic commands ###
