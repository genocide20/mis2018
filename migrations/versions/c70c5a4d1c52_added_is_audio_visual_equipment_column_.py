"""Added is_audio_visual_equipment column in ProcurementDetail model

Revision ID: c70c5a4d1c52
Revises: 1fde9934bc75
Create Date: 2023-04-12 08:50:01.772000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c70c5a4d1c52'
down_revision = '1fde9934bc75'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procurement_details', sa.Column('is_audio_visual_equipment', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('procurement_details', 'is_audio_visual_equipment')
    # ### end Alembic commands ###