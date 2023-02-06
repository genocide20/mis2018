"""Added survey date in ProcurementSurveyComputer model

Revision ID: e9b1b48cd42d
Revises: 35e2030a8253
Create Date: 2023-02-06 16:40:21.851000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9b1b48cd42d'
down_revision = '35e2030a8253'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procurement_info_computers', sa.Column('computer_name', sa.String(), nullable=True))
    op.add_column('procurement_info_computers', sa.Column('survey_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'procurement_info_computers', 'procurement_survey_computers', ['survey_id'], ['id'])
    op.add_column('procurement_survey_computers', sa.Column('survey_date', sa.DateTime(timezone=True), server_default=sa.text(u'now()'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('procurement_survey_computers', 'survey_date')
    op.drop_constraint(None, 'procurement_info_computers', type_='foreignkey')
    op.drop_column('procurement_info_computers', 'survey_id')
    op.drop_column('procurement_info_computers', 'computer_name')
    # ### end Alembic commands ###
