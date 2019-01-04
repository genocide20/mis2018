from ..main import db, ma

class AssetItem(db.Model):
    __tablename__ = 'asset_items'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('desc', db.String(255), nullable=False)
    location = db.Column('location', db.String(255))
    value = db.Column('cost', db.Numeric())
    purchased_at = db.Column('purchased_at', db.Date())
    retired_at = db.Column('retired_at', db.Date())
    group_id = db.Column('group_id', db.String(2), nullable=False)
    class_id = db.Column('class_id', db.String(2), nullable=False)
    type_id = db.Column('type_id', db.String(3), nullable=False)
    desc_id = db.Column('desc_id', db.String(4), nullable=False)
    room_id = db.Column('room_id', db.ForeignKey('scheduler_room_resources.id'))
