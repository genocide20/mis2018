# -*- coding:utf-8 -*-
from app.main import db


class HealthServiceSite(db.Model):
    __tablename__ = 'health_service_sites'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, info={'label': 'Site Name'})
    lat = db.Column(db.Float(), info={'label': 'Latitude'})
    lon = db.Column(db.Float(), info={'label': 'Longitude'})


class HealthServiceService(db.Model):
    __tablename__ = 'health_service_services'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, info={'label': 'Service'})
    detail = db.Column(db.Text(), nullable=True, info={'label': 'Detail'})


class HealthServiceTimeSlot(db.Model):
    __tablename__ = 'health_service_timeslots'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start = db.Column('start', db.DateTime(timezone=True), nullable=False, info={'label': u'เริ่ม'})
    end = db.Column('end', db.DateTime(timezone=True), nullable=False, info={'label': u'สิ้นสุด'})
    service_id = db.Column(db.ForeignKey('health_service_services.id'))
    site_id = db.Column(db.ForeignKey('health_service_sites.id'))
    staff_id = db.Column(db.ForeignKey('staff_account.id'), nullable=False)
    created_by = db.relationship('StaffAccount')
    quota = db.Column(db.Integer, info={'label': 'Quota'})
    cancelled_at = db.Column(db.DateTime(timezone=True))

    site = db.relationship(HealthServiceSite, backref=db.backref('bookings'))
    service = db.relationship(HealthServiceService, backref=db.backref('bookings'))


class HealthServiceBooking(db.Model):
    __tablename__ = 'health_service_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slot_id = db.Column(db.ForeignKey('health_service_timeslots.id'))
    slot = db.relationship(HealthServiceTimeSlot, backref=db.backref('bookings'))
    cancelled = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(db.DateTime(timezone=True))
    confirmed_at = db.Column(db.DateTime(timezone=True))
