"""added google ID field to the room event model

Revision ID: 32d2449aee31
Revises: 046b07fdebb1
Create Date: 2019-02-11 17:16:38.934283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32d2449aee31'
down_revision = '046b07fdebb1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scheduler_room_reservations', sa.Column('google_event_id', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scheduler_room_reservations', 'google_event_id')
    # ### end Alembic commands ###