# -*- coding:utf-8 -*-
from flask_login import login_required, current_user

from models import (StaffAccount, StaffPersonalInfo,
                    StaffLeaveRequest, StaffLeaveQuota, StaffLeaveApprover, StaffLeaveApproval, StaffLeaveType,
                    StaffWorkFromHomeRequest, StaffLeaveRequestSchema,
                    StaffWorkFromHomeJobDetail, StaffWorkFromHomeApprover, StaffWorkFromHomeApproval,
                    StaffWorkFromHomeCheckedJob, StaffWorkFromHomeRequestSchema, StaffLeaveRemainQuota)
from . import staffbp as staff
from app.main import db, get_weekdays, mail
from app.models import Holidays, Org
from flask import jsonify, render_template, request, redirect, url_for, flash
from datetime import date, datetime
from collections import defaultdict, namedtuple
import pytz
from sqlalchemy import and_
from werkzeug.utils import secure_filename
from app.auth.views import line_bot_api
from linebot.models import TextSendMessage
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive
import requests
import os
from flask_mail import Message

gauth = GoogleAuth()
keyfile_dict = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()
scopes = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scopes)
drive = GoogleDrive(gauth)

tz = pytz.timezone('Asia/Bangkok')

#TODO: remove hardcoded annual quota soon
LEAVE_ANNUAL_QUOTA = 10

today = datetime.today()
if today.month >= 10:
    START_FISCAL_DATE = datetime(today.year,10,1)
    END_FISCAL_DATE = datetime(today.year+1,9,30)
else:
    START_FISCAL_DATE = datetime(today.year-1,10,1)
    END_FISCAL_DATE = datetime(today.year,9,30)



def get_start_end_date_for_fiscal_year(fiscal_year):
    '''Find start and end date from a given fiscal year.

    :param fiscal_year:  fiscal year
    :return: date
    '''
    start_date = date(fiscal_year - 1, 10, 1)
    end_date = date(fiscal_year, 9, 30)
    return start_date, end_date

def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=[recp])
    mail.send(message)


@staff.route('/')
@login_required
def index():
    return render_template('staff/index.html')


@staff.route('/person/<int:account_id>')
def show_person_info(account_id=None):
    if account_id:
        account = StaffAccount.query.get(account_id)
        return render_template('staff/info.html', person=account)


@staff.route('/api/list/')
@staff.route('/api/list/<int:account_id>')
def get_staff(account_id=None):
    data = []
    if not account_id:
        accounts = StaffAccount.query.all()
        for account in accounts:
            data.append({
                'email': account.email,
                'firstname': account.personal_info.en_firstname,
                'lastname': account.personal_info.en_lastname,
            })
    else:
        account = StaffAccount.query.get(account_id)
        if account:
            data = [{
                'email': account.email,
                'firstname': account.personal_info.en_firstname,
                'lastname': account.personal_info.en_lastname,
            }]
        else:
            return jsonify(data), 401
    return jsonify(data), 200


@staff.route('/set_password', methods=['GET', 'POST'])
def set_password():
    if request.method == 'POST':
        email = request.form.get('email', None)
        return email
    return render_template('staff/set_password.html')


@staff.route('/leave/info')
@login_required
def show_leave_info():
    Quota = namedtuple('quota', ['id', 'limit'])
    cum_days = defaultdict(float)
    quota_days = defaultdict(float)
    for req in current_user.leave_requests:
        used_quota = current_user.personal_info.get_total_leaves(req.quota.id, tz.localize(START_FISCAL_DATE),
                                                                 tz.localize(END_FISCAL_DATE))
        leave_type = unicode(req.quota.leave_type)
        cum_days[leave_type] = used_quota
    
    for quota in current_user.personal_info.employment.quota:
        delta = current_user.personal_info.get_employ_period()
        max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
        last_quota = StaffLeaveRemainQuota.query.filter(and_(StaffLeaveRemainQuota.leave_quota_id == quota.id,
                                            StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
        if delta.years > 0:
            if max_cum_quota:
                if last_quota:
                    last_year_quota = last_quota.last_year_quota
                else:
                    last_year_quota = 0
                before_get_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
                quota_limit = max_cum_quota if max_cum_quota < before_get_max_quota else before_get_max_quota
            else:
                quota_limit = quota.max_per_year
        else:
            if delta.months > 5:
                quota_limit = quota.first_year
            else:
                quota_limit = quota.first_year if not quota.min_employed_months else 0
        quota_days[quota.leave_type.type_] = Quota(quota.id, quota_limit)

    return render_template('staff/leave_info.html', cum_days=cum_days, quota_days=quota_days)


@staff.route('/leave/request/quota/<int:quota_id>',
             methods=['GET', 'POST'])
@login_required
def request_for_leave(quota_id=None):
    if request.method == 'POST':
        form = request.form
        if quota_id:
            quota = StaffLeaveQuota.query.get(quota_id)
            if quota:
                start_dt, end_dt = form.get('dates').split(' - ')
                start_datetime = datetime.strptime(start_dt, '%m/%d/%Y')
                end_datetime = datetime.strptime(end_dt, '%m/%d/%Y')
                req = StaffLeaveRequest(
                    start_datetime=tz.localize(start_datetime),
                    end_datetime=tz.localize(end_datetime)
                )
                if form.get('traveldates'):
                    start_travel_dt, end_travel_dt = form.get('traveldates').split(' - ')
                    start_travel_datetime = datetime.strptime(start_travel_dt, '%m/%d/%Y')
                    end_travel_datetime = datetime.strptime(end_travel_dt, '%m/%d/%Y')
                    if not (start_travel_datetime <= start_datetime and end_travel_datetime >= end_datetime):
                        flash(u'ช่วงเวลาเดินทาง ไม่ครอบคลุมวันที่ต้องการขอลา กรุณาตรวจสอบอีกครั้ง', "danger")
                        return redirect(request.referrer)
                    else:
                        req.start_travel_datetime = tz.localize(start_travel_datetime)
                        req.end_travel_datetime = tz.localize(end_travel_datetime)
                upload_file = request.files.get('document')
                after_hour = True if form.getlist("after_hour") else False
                if upload_file:
                    upload_file_name = secure_filename(upload_file.filename)
                    upload_file.save(upload_file_name)
                    file_drive = drive.CreateFile({'title':upload_file_name, 'parents':['106Dg12ecMn7_nnY8eF5veQoWrCP-xDXx']})
                    file_drive.SetContentFile(upload_file_name)
                    file_drive.Upload()
                    permission = file_drive.InsertPermission({'type':'anyone','value':'anyone','role':'reader'})
                    upload_file_id = file_drive['id']
                else:
                    upload_file_id = None
                if start_datetime.date() <= END_FISCAL_DATE.date() and end_datetime.date() > END_FISCAL_DATE.date() :
                    flash(u'ไม่สามารถลาข้ามปีงบประมาณได้ กรุณาส่งคำร้องแยกกัน 2 ครั้ง โดยแยกตามปีงบประมาณ')
                    return redirect(request.referrer)
                delta = start_datetime.date() - datetime.today().date()
                if delta.days > 0 and not quota.leave_type.request_in_advance:
                    flash(u'ไม่สามารถลาล่วงหน้าได้ กรุณาลองใหม่')
                    return redirect(request.referrer)
                    # retrieve cum periods
                used_quota = current_user.personal_info.get_total_leaves(quota.id, tz.localize(START_FISCAL_DATE),
                                                                         tz.localize(END_FISCAL_DATE))
                req_duration = get_weekdays(req)
                holidays = Holidays.query.filter(and_(Holidays.holiday_date >= start_datetime,
                                                      Holidays.holiday_date <= end_datetime)).all()
                req_duration = req_duration - len(holidays)
                delta = current_user.personal_info.get_employ_period()
                if req_duration == 0:
                    flash(u'วันลาตรงกับวันหยุด')
                    return redirect(request.referrer)
                if quota.max_per_leave:
                    if req_duration >= quota.max_per_leave and upload_file_id is None:
                        flash(
                            u'ไม่สามารถลาป่วยเกินสามวันได้โดยไม่มีใบรับรองแพทย์ประกอบ')
                        return redirect(request.referrer)
                    else:
                        if delta.years > 0:
                            quota_limit = quota.max_per_year
                        else:
                            quota_limit = quota.first_year
                else:
                    max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
                    if delta.years > 0:
                        if max_cum_quota:
                            if start_datetime.date() > END_FISCAL_DATE.date():
                                quota_limit = LEAVE_ANNUAL_QUOTA
                            else:
                                last_quota = StaffLeaveRemainQuota.query.filter(and_
                                        (StaffLeaveRemainQuota.leave_quota_id == quota.id,
                                        StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
                                if last_quota:
                                    last_year_quota = last_quota.last_year_quota
                                else:
                                    last_year_quota = 0
                                before_cut_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
                                quota_limit = max_cum_quota if max_cum_quota < before_cut_max_quota else before_cut_max_quota
                        else:
                            quota_limit = quota.max_per_year
                    else:
                        # skip min employ month of annual leave because leave req button doesn't appear
                        quota_limit = quota.first_year
                req.quota = quota
                req.staff = current_user
                req.reason = form.get('reason')
                req.contact_address = form.get('contact_addr')
                req.contact_phone = form.get('contact_phone')
                req.total_leave_days = req_duration
                req.upload_file_url = upload_file_id
                req.after_hour = after_hour
                if used_quota + req_duration <= quota_limit:
                    if form.getlist('notified_by_line'):
                        req.notify_to_line = True
                    db.session.add(req)
                    db.session.commit()
                    for approver in StaffLeaveApprover.query.filter_by(staff_account_id=current_user.id):
                        if approver.account.notified_by_line:
                            req_msg = u'{} ขออนุมัติลา คลิกที่ Link เพื่อดูรายละเอียดเพิ่มเติม {} :'.format(current_user.personal_info.fullname,
                                                url_for("staff.pending_leave_approval", req_id=req.id, _external=True))
                            if os.environ["FLASK_ENV"] == "production":
                                line_bot_api.push_message(to=approver.account.line_id,messages=TextSendMessage(text=req_msg))
                            else:
                                print(req_msg, approver.account.id)
                        req_title = u'แจ้งการขออนุมัติ'+req.quota.leave_type.type_
                        req_msg = u'{} ขออนุมัติลา คลิกที่ Link เพื่อดูรายละเอียดเพิ่มเติม {} \n\n\nหน่วยพัฒนาบุคลากรและการเจ้าหน้าที่'\
                            .format(current_user.personal_info.fullname,
                                        url_for("staff.pending_leave_approval", req_id=req.id, _external=True))
                        send_msg = send_mail(approver.account.email+"@mahidol.ac.th", req_title, req_msg)
                    return redirect(url_for('staff.show_leave_info'))
                else:
                    flash(u'วันลาที่ต้องการลา เกินจำนวนวันลาคงเหลือ')
                    return redirect(request.referrer)
            else:
                return 'Error happened'
    else:
        quota = StaffLeaveQuota.query.get(quota_id)
        holidays = [h.tojson()['date'] for h in Holidays.query.all()]
        return render_template('staff/leave_request.html', errors={}, quota=quota, holidays=holidays)


@staff.route('/leave/request/quota/period/<int:quota_id>', methods=["POST", "GET"])
@login_required
def request_for_leave_period(quota_id=None):
    if request.method == 'POST':
        form = request.form
        if quota_id:
            quota = StaffLeaveQuota.query.get(quota_id)
            if quota:
                # retrieve cum periods
                used_quota = current_user.personal_info.get_total_leaves(quota.id, tz.localize(START_FISCAL_DATE),
                                                                         tz.localize(END_FISCAL_DATE))
                start_t, end_t = form.get('times').split(' - ')
                start_dt = '{} {}'.format(form.get('dates'), start_t)
                end_dt = '{} {}'.format(form.get('dates'), end_t)
                start_datetime = datetime.strptime(start_dt, '%m/%d/%Y %H:%M')
                end_datetime = datetime.strptime(end_dt, '%m/%d/%Y %H:%M')
                if not quota.leave_type.request_in_advance:
                    flash(u'ไม่สามารถลาล่วงหน้าได้ กรุณาลองใหม่')
                    return redirect(request.referrer)
                req = StaffLeaveRequest(
                    start_datetime=tz.localize(start_datetime),
                    end_datetime=tz.localize(end_datetime)
                )
                req_duration = get_weekdays(req)
                if req_duration == 0:
                    flash(u'วันลาตรงกับเสาร์-อาทิตย์')
                    return redirect(request.referrer)
                holidays = Holidays.query.filter(Holidays.holiday_date == start_datetime.date()).all()
                req_duration = req_duration - len(holidays)
                if req_duration <= 0:
                    flash(u'วันลาตรงกับวันหยุด')
                    return redirect(request.referrer)
                delta = current_user.personal_info.get_employ_period()
                last_quota = StaffLeaveRemainQuota.query.filter(and_
                                                                (StaffLeaveRemainQuota.leave_quota_id == quota.id,
                                                    StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
                max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
                if delta.years > 0:
                    if max_cum_quota:
                        if last_quota:
                            last_year_quota = last_quota.last_year_quota
                        else:
                            last_year_quota = 0
                        before_cut_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
                        quota_limit = max_cum_quota if max_cum_quota < before_cut_max_quota else before_cut_max_quota
                    else:
                        quota_limit = quota.max_per_year
                else:
                    quota_limit = quota.first_year
                req.quota = quota
                req.staff = current_user
                req.reason = form.get('reason')
                req.contact_address = form.get('contact_addr')
                req.contact_phone = form.get('contact_phone')
                req.total_leave_days = req_duration
                if used_quota + req_duration <= quota_limit:
                    if form.getlist('notified_by_line'):
                        req.notify_to_line = True
                    db.session.add(req)
                    db.session.commit()
                    if form.getlist('notified_by_line'):
                        for approver in StaffLeaveApprover.query.filter_by(staff_account_id=current_user.id):
                            req_msg = u'{} ขออนุมัติลา รายละเอียดเพิ่มเติม {} :'.format(
                                current_user.personal_info.fullname,
                                url_for("staff.pending_leave_approval", req_id=req.id, _external=True))
                            if os.environ["FLASK_ENV"] == "production":
                                line_bot_api.push_message(to=approver.account.line_id,
                                                          messages=TextSendMessage(text=req_msg))
                            else:
                                print(req_msg, approver.account.id)
                        req_title = u'แจ้งการขออนุมัติ'+req.quota.leave_type.type_
                        req_msg = u'{} ขออนุมัติลา คลิกที่ Link เพื่อดูรายละเอียดเพิ่มเติม {} \n\n\nหน่วยพัฒนาบุคลากรและการเจ้าหน้าที่'\
                            .format(current_user.personal_info.fullname,
                                        url_for("staff.pending_leave_approval", req_id=req.id, _external=True))
                        send_msg = send_mail(approver.account.email+"@mahidol.ac.th", req_title, req_msg)
                    return redirect(url_for('staff.show_leave_info'))
                else:
                    flash(u'วันลาที่ต้องการลา เกินจำนวนวันลาคงเหลือ')
                    return redirect(request.referrer)
            else:
                return 'Error happened'
    else:
        quota = StaffLeaveQuota.query.get(quota_id)
        holidays = [h.tojson()['date'] for h in Holidays.query.all()]
        return render_template('staff/leave_request_period.html', errors={}, quota=quota, holidays=holidays)


@staff.route('/leave/request/info/<int:quota_id>')
@login_required
def request_for_leave_info(quota_id=None):
    quota = StaffLeaveQuota.query.get(quota_id)
    leaves = []
    fiscal_years = set()
    for leave in current_user.leave_requests:
        if leave.start_datetime >= tz.localize(START_FISCAL_DATE) and leave.end_datetime <= tz.localize(END_FISCAL_DATE):
            if leave.quota == quota:
                leaves.append(leave)
        if leave.start_datetime.month in [10,11,12]:
            fiscal_years.add(leave.start_datetime.year + 1)
        else:
            fiscal_years.add(leave.start_datetime.year)
    used_quota = current_user.personal_info.get_total_leaves(quota.id, tz.localize(START_FISCAL_DATE),
                                                                 tz.localize(END_FISCAL_DATE))

    delta = current_user.personal_info.get_employ_period()
    max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
    if delta.years > 0:
        if max_cum_quota:
            last_quota = StaffLeaveRemainQuota.query.filter(and_
                            (StaffLeaveRemainQuota.leave_quota_id == quota.id,
                            StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
            if last_quota:
                last_year_quota = last_quota.last_year_quota
            else:
                last_year_quota = 0
            before_cut_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
            quota_limit = max_cum_quota if max_cum_quota < before_cut_max_quota else before_cut_max_quota
        else:
            quota_limit = quota.max_per_year
    else:
        quota_limit = quota.first_year
    return render_template('staff/request_info.html', leaves=leaves, quota=quota,
                           fiscal_years=fiscal_years, quota_limit=quota_limit, used_quota=used_quota)


@staff.route('/leave/request/info/<int:quota_id>/others_year/<int:fiscal_year>')
@login_required
def request_for_leave_info_others_fiscal(quota_id=None, fiscal_year=None):
    quota = StaffLeaveQuota.query.get(quota_id)
    leaves = []
    for leave in current_user.leave_requests:
        if leave.start_datetime.month in [10,11,12]:
            fiscal_years = leave.start_datetime.year + 1
        else:
            fiscal_years = leave.start_datetime.year

        if fiscal_year == fiscal_years:
            if leave.quota == quota:
                leaves.append(leave)
                fiscal_year = fiscal_year

    requester = StaffLeaveApprover.query.filter_by(staff_account_id=current_user.id)

    return render_template('staff/leave_info_others_fiscal_year.html', leaves=leaves, reqester=requester, quota=quota,
                           fiscal_year=fiscal_year)


@staff.route('/leave/request/edit/<int:req_id>',
             methods=['GET', 'POST'])
@login_required
def edit_leave_request(req_id=None):
    req = StaffLeaveRequest.query.get(req_id)
    if req.total_leave_days == 0.5:
        return redirect(url_for("staff.edit_leave_request_period", req_id=req_id))
    if request.method == 'POST':
        quota = req.quota
        if quota:
            start_dt, end_dt = request.form.get('dates').split(' - ')
            start_datetime = datetime.strptime(start_dt, '%m/%d/%Y')
            end_datetime = datetime.strptime(end_dt, '%m/%d/%Y')
            if start_datetime <= END_FISCAL_DATE and end_datetime > END_FISCAL_DATE:
                flash(u'ไม่สามารถลาข้ามปีงบประมาณได้ กรุณาส่งคำร้องแยกกัน 2 ครั้ง โดยแยกตามปีงบประมาณ')
                return redirect(request.referrer)
            delta = start_datetime.date() - datetime.today().date()
            if delta.days > 0 and not quota.leave_type.request_in_advance:
                flash(u'ไม่สามารถลาล่วงหน้าได้ กรุณาลองใหม่')
                return redirect(request.referrer)
                # retrieve cum periods
            used_quota = current_user.personal_info.get_total_leaves(quota.id, tz.localize(START_FISCAL_DATE),
                                                                     tz.localize(END_FISCAL_DATE))

            req.start_datetime = tz.localize(start_datetime)
            req.end_datetime = tz.localize(end_datetime)
            req_duration = get_weekdays(req)
            holidays = Holidays.query.filter(and_(Holidays.holiday_date >= start_datetime,
                                                  Holidays.holiday_date <= end_datetime)).all()
            req_duration = req_duration - len(holidays)
            delta = current_user.personal_info.get_employ_period()
            if req_duration == 0:
                flash(u'วันลาตรงกับวันหยุด')
                return redirect(request.referrer)
            if quota.max_per_leave:
                if req_duration > quota.max_per_leave:
                    flash(
                        u'ไม่สามารถลาป่วยเกินสามวันได้โดยไม่มีใบรับรองแพทย์ประกอบ กรุณาติดต่อหน่วยพัฒนาบุคลากรและการเจ้าหน้าที่(HR)')
                    return redirect(request.referrer)
                else:
                    if delta.years > 0:
                        quota_limit = quota.max_per_year
                    else:
                        quota_limit = quota.first_year
            else:
                max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
                if delta.years > 0:
                    if max_cum_quota:
                        if start_datetime > END_FISCAL_DATE:
                            quota_limit = LEAVE_ANNUAL_QUOTA
                        else:
                            last_quota = StaffLeaveRemainQuota.query.filter(and_
                                        (StaffLeaveRemainQuota.leave_quota_id == quota.id,
                                        StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
                            if last_quota:
                                last_year_quota = last_quota.last_year_quota
                            else:
                                last_year_quota = 0
                            before_cut_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
                            quota_limit = max_cum_quota if max_cum_quota < before_cut_max_quota else before_cut_max_quota
                    else:
                        quota_limit = quota.max_per_year
                else:
                    quota_limit = quota.first_year

            req.reason = request.form.get('reason')
            req.contact_address = request.form.get('contact_addr'),
            req.contact_phone = request.form.get('contact_phone'),
            req.total_leave_days = req_duration
            if used_quota + req_duration <= quota_limit:
                db.session.add(req)
                db.session.commit()
                return redirect(url_for('staff.show_leave_info'))
            else:
                flash(u'วันลาที่ต้องการลา เกินจำนวนวันลาคงเหลือ')
                return redirect(request.referrer)
        else:
            return 'Error happened'

    selected_dates = [req.start_datetime, req.end_datetime]
    return render_template('staff/edit_leave_request.html', selected_dates=selected_dates, req=req, errors={})


@staff.route('/leave/request/edit/period/<int:req_id>',
             methods=['GET', 'POST'])
@login_required
def edit_leave_request_period(req_id=None):
    req = StaffLeaveRequest.query.get(req_id)
    if request.method == 'POST':
        quota = req.quota
        if quota:
            used_quota = current_user.personal_info.get_total_leaves(quota.id, tz.localize(START_FISCAL_DATE),
                                                                     tz.localize(END_FISCAL_DATE))
            start_t, end_t = request.form.get('times').split(' - ')
            start_dt = '{} {}'.format(request.form.get('dates'), start_t)
            end_dt = '{} {}'.format(request.form.get('dates'), end_t)
            start_datetime = datetime.strptime(start_dt, '%m/%d/%Y %H:%M')
            end_datetime = datetime.strptime(end_dt, '%m/%d/%Y %H:%M')
            delta = start_datetime - datetime.today()
            if delta.days > 0 and not quota.leave_type.request_in_advance:
                flash(u'ไม่สามารถลาล่วงหน้าได้ กรุณาลองใหม่')
                return redirect(request.referrer)
            holidays = Holidays.query.filter(Holidays.holiday_date == start_datetime.date()).all()
            if len(holidays) > 0:
                flash(u'วันลาตรงกับวันหยุด')
                return redirect(request.referrer)
            req.start_datetime = tz.localize(start_datetime)
            req.end_datetime = tz.localize(end_datetime)
            req_duration = get_weekdays(req)
            if req_duration == 0:
                flash(u'วันลาตรงกับเสาร์-อาทิตย์')
                return redirect(request.referrer)
            # if duration not exceeds quota
            delta = current_user.personal_info.get_employ_period()
            last_quota = StaffLeaveRemainQuota.query.filter(and_
                                                            (StaffLeaveRemainQuota.leave_quota_id == quota.id,
                                                             StaffLeaveRemainQuota.year == START_FISCAL_DATE.year)).first()
            max_cum_quota = current_user.personal_info.get_max_cum_quota_per_year(quota)
            if delta.years > 0:
                if max_cum_quota:
                    if last_quota:
                        last_year_quota = last_quota.last_year_quota
                    else:
                        last_year_quota = 0
                    before_cut_max_quota = last_year_quota + LEAVE_ANNUAL_QUOTA
                    quota_limit = max_cum_quota if max_cum_quota < before_cut_max_quota else before_cut_max_quota
                else:
                    quota_limit = quota.max_per_year
            else:
                quota_limit = quota.first_year
            req.reason = request.form.get('reason')
            req.contact_address = request.form.get('contact_addr')
            req.contact_phone = request.form.get('contact_phone')
            req.total_leave_days = req_duration
            if used_quota + req_duration <= quota_limit:
                db.session.add(req)
                db.session.commit()
                return redirect(url_for('staff.show_leave_info'))
            else:
                flash(u'วันลาที่ต้องการลา เกินจำนวนวันลาคงเหลือ')
                return redirect(request.referrer)
        else:
            return 'Error happened'

    selected_dates = [req.start_datetime]

    return render_template('staff/edit_leave_request_period.html', req=req, selected_dates=selected_dates, errors={})


@staff.route('/leave/requests/approval/info')
@login_required
def show_leave_approval_info():
    leave_types = StaffLeaveType.query.all()
    requesters = StaffLeaveApprover.query.filter_by(approver_account_id=current_user.id).all()
    requester_cum_periods = {}
    for requester in requesters:
        cum_periods = defaultdict(float)
        for leave_request in requester.requester.leave_requests:
            if leave_request.cancelled_at is None and leave_request.get_approved:
                cum_periods[leave_request.quota.leave_type] += leave_request.total_leave_days
        requester_cum_periods[requester] = cum_periods

    return render_template('staff/leave_request_approval_info.html',
                           requesters=requesters,
                           requester_cum_periods=requester_cum_periods,
                           leave_types=leave_types)


@staff.route('/leave/requests/approval/pending/<int:req_id>')
@login_required
def pending_leave_approval(req_id):
    req = StaffLeaveRequest.query.get(req_id)
    approver = StaffLeaveApprover.query.filter_by(account=current_user, requester=req.staff).first()
    return render_template('staff/leave_request_pending_approval.html', req=req, approver=approver)


@staff.route('/leave/requests/approve/<int:req_id>/<int:approver_id>', methods=['GET','POST'])
@login_required
def leave_approve(req_id, approver_id):
    approved = request.args.get("approved")
    if request.method == 'POST':
        comment = request.form.get('approval_comment')
        approval = StaffLeaveApproval(
            request_id=req_id,
            approver_id=approver_id,
            is_approved=True if approved == 'yes' else False,
            updated_at=tz.localize(datetime.today()),
            approval_comment = comment if comment != "" else None
        )
        db.session.add(approval)
        db.session.commit()
        flash(u'อนุมัติการลาให้บุคลากรในสังกัดเรียบร้อย')
        req = StaffLeaveRequest.query.get(req_id)
        if req.notify_to_line:
            approve_msg = u'การขออนุมัติลา{} ได้รับการพิจารณาโดย {} เรียบร้อยแล้ว รายละเอียดเพิ่มเติม {}'.format(req.quota.leave_type.type_,
                                                                        current_user.personal_info.fullname,
                                                    url_for("staff.show_leave_approval" ,req_id=req_id, _external=True))
            if os.environ["FLASK_ENV"] == "production":
                line_bot_api.push_message(to=req.staff.line_id, messages=TextSendMessage(text=approve_msg))
            else:
                print(approve_msg, req.staff.id)
        approve_title = u'แจ้งสถานะการอนุมัติ' + req.quota.leave_type.type_
        approve_msg = u'การขออนุมัติลา{} ได้รับการพิจารณาโดย {} เรียบร้อยแล้ว รายละเอียดเพิ่มเติม {}'.format(
            req.quota.leave_type.type_,
            current_user.personal_info.fullname,
            url_for("staff.show_leave_approval", req_id=req_id, _external=True))
        send_msg = send_mail(req.staff.email + "@mahidol.ac.th", approve_title, approve_msg)
        return redirect(url_for('staff.show_leave_approval_info'))
    if approved is not None:
        return render_template('staff/leave_request_approval_comment.html')
    else:
        return redirect(url_for('staff.pending_leave_approval', req_id=req_id))


@staff.route('/leave/requests/<int:req_id>/approvals')
@login_required
def show_leave_approval(req_id):
    req = StaffLeaveRequest.query.get(req_id)
    approvers = StaffLeaveApprover.query.filter_by(staff_account_id=current_user.id)
    return render_template('staff/leave_approval_status.html', req=req, approvers=approvers)


@staff.route('/leave/requests/<int:req_id>/cancel')
@login_required
def cancel_leave_request(req_id):
    req = StaffLeaveRequest.query.get(req_id)
    req.cancelled_at = tz.localize(datetime.today())
    db.session.add(req)
    db.session.commit()
    return redirect(request.referrer)


@staff.route('/leave/requests/approved/info/<int:requester_id>')
@login_required
def show_leave_approval_info_each_person(requester_id):
    requester = StaffLeaveRequest.query.filter_by(staff_account_id=requester_id)
    return render_template('staff/leave_request_approved_each_person.html', requester=requester)


@staff.route('leave/<int:request_id>/record/info',
             methods=['GET', 'POST'])
@login_required
def record_each_request_leave_request(request_id):
    req = StaffLeaveRequest.query.get(request_id)
    return render_template('staff/leave_record_info.html', req=req)


@staff.route('/leave/requests/search')
@login_required
def search_leave_request_info():
    reqs = StaffLeaveRequest.query.all()
    record_schema = StaffLeaveRequestSchema(many=True)
    return jsonify(record_schema.dump(reqs).data)


@staff.route('/leave/requests')
@login_required
def leave_request_info():
    return render_template('staff/leave_request_info.html')


@staff.route('/wfh/requests/search')
@login_required
def search_wfh_request_info():
    reqs = StaffWorkFromHomeRequest.query.all()
    record_schema = StaffWorkFromHomeRequestSchema(many=True)
    return jsonify(record_schema.dump(reqs).data)


@staff.route('/wfh/requests')
@login_required
def wfh_request_info():
    return render_template('staff/wfh_list.html')


@staff.route('/leave/requests/result-by-date',
                    methods=['GET', 'POST'])
@login_required
def leave_request_result_by_date():
    if request.method == 'POST':
        form = request.form

        start_dt, end_dt = form.get('dates').split(' - ')
        start_date = datetime.strptime(start_dt, '%m/%d/%Y')
        end_date = datetime.strptime(end_dt, '%m/%d/%Y')

        leaves = StaffLeaveRequest.query.filter(and_(StaffLeaveRequest.start_datetime>=start_date,
                                                     StaffLeaveRequest.end_datetime<=end_date))
        return render_template('staff/leave_request_result_by_date.html', leaves=leaves,
                               start_date=start_date.date(), end_date=end_date.date())
    else:
        return render_template('staff/leave_request_info_by_date.html')


@staff.route('/leave/requests/result-by-person',
                    methods=['GET', 'POST'])
@login_required
def leave_request_result_by_person():
    org_id = request.args.get('deptid')
    fiscal_year = request.args.get('fiscal_year')
    if fiscal_year is not None:
        start_date, end_date = get_start_end_date_for_fiscal_year(int(fiscal_year))
    else:
        start_date = None
        end_date = None
    years = set()
    leaves_list = []
    departments = Org.query.all()
    leave_types = [t.type_ for t in StaffLeaveType.query.all()]
    if org_id is None:
        account_query = StaffAccount.query.all()
    else:
        account_query = StaffAccount.query.filter(StaffAccount.personal_info.has(org_id=org_id))

    for account in account_query:
        record = {}
        record["staffid"] = account.id
        record["fullname"] = account.personal_info.fullname
        record["total"] = 0
        if account.personal_info.org:
            record["org"] = account.personal_info.org.name
        else:
            record["org"] = ""
        for leave_type in leave_types:
            record[leave_type] = 0
        for req in account.leave_requests:
            years.add(req.start_datetime.year)
            if start_date and end_date:
                if req.start_datetime.date()<start_date or req.start_datetime.date()>end_date:
                    continue
            leave_type = req.quota.leave_type.type_
            record[leave_type] += req.total_leave_days
            record["total"] += req.total_leave_days
        leaves_list.append(record)
    years = sorted(years)
    if len(years) > 0:
        years.append(years[-1]+1)
        years.insert(0, years[0]-1)
    return render_template('staff/leave_request_by_person.html', leave_types = leave_types,
                           sel_dept=org_id, year=fiscal_year,
                           leaves_list=leaves_list, departments=[{'id': d.id, 'name': d.name}
                                                                 for d in departments], years=years)


@staff.route('leave/requests/result-by-person/<int:requester_id>')
@login_required
def leave_request_by_person_detail(requester_id):
    requester = StaffLeaveRequest.query.filter_by(staff_account_id=requester_id)
    return render_template('staff/leave_request_by_person_detail.html', requester=requester)


@staff.route('/wfh')
@login_required
def show_work_from_home():
    req = StaffWorkFromHomeRequest.query.filter_by(staff_account_id=current_user.id).all()
    checkjob = StaffWorkFromHomeCheckedJob.query.all()
    return render_template('staff/wfh_info.html', req=req, checkjob=checkjob)


@staff.route('/wfh/request',
             methods=['GET', 'POST'])
@login_required
def request_work_from_home():
    if request.method == 'POST':
        form = request.form

        start_dt, end_dt = form.get('dates').split(' - ')
        start_datetime = datetime.strptime(start_dt, '%m/%d/%Y')
        end_datetime = datetime.strptime(end_dt, '%m/%d/%Y')
        req = StaffWorkFromHomeRequest(
            staff=current_user,
            start_datetime=tz.localize(start_datetime),
            end_datetime=tz.localize(end_datetime),
            detail=form.get('detail'),
            contact_phone=form.get('contact_phone'),
            deadline_date=form.get('deadline_date')
        )
        db.session.add(req)
        db.session.commit()
        return redirect(url_for('staff.show_work_from_home'))

    else:
        return render_template('staff/wfh_request.html')


@staff.route('/wfh/request/<int:request_id>/edit',
             methods=['GET', 'POST'])
@login_required
def edit_request_work_from_home(request_id):
    req = StaffWorkFromHomeRequest.query.get(request_id)
    if request.method == 'POST':
        start_dt, end_dt = request.form.get('dates').split(' - ')
        start_datetime = datetime.strptime(start_dt, '%m/%d/%Y')
        end_datetime = datetime.strptime(end_dt, '%m/%d/%Y')
        req.start_datetime = tz.localize(start_datetime),
        req.end_datetime = tz.localize(end_datetime),
        req.detail = request.form.get('detail'),
        req.contact_phone = request.form.get('contact_phone'),
        req.deadline_date = request.form.get('deadline_date')
        db.session.add(req)
        db.session.commit()
        return redirect(url_for('staff.show_work_from_home'))

    selected_dates = [req.start_datetime, req.end_datetime]
    deadline = req.deadline_date
    return render_template('staff/edit_wfh_request.html', req=req, selected_dates=selected_dates, deadline=deadline)


@staff.route('/wfh/request/<int:request_id>/cancel')
@login_required
def cancel_wfh_request(request_id):
    req = StaffWorkFromHomeRequest.query.get(request_id)
    req.cancelled_at = tz.localize(datetime.today())
    db.session.add(req)
    db.session.commit()
    return redirect(request.referrer)


@staff.route('/wfh/<int:request_id>/info',
             methods=['GET', 'POST'])
@login_required
def wfh_show_request_info(request_id):
    if request.method == 'POST':
        form = request.form
        req = StaffWorkFromHomeJobDetail(
            wfh_id=request_id,
            activity=form.get('activity')
        )
        db.session.add(req)
        db.session.commit()
        wfhreq = StaffWorkFromHomeRequest.query.get(request_id)
        detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
        return render_template('staff/wfh_request_job_details.html', wfhreq=wfhreq, detail=detail)
    else:
        check = StaffWorkFromHomeCheckedJob.query.filter_by(request_id=request_id).first()
        if check:
            return redirect(url_for("staff.record_each_request_wfh_request", request_id=request_id))
        else:
            wfhreq = StaffWorkFromHomeRequest.query.get(request_id)
            detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
            return render_template('staff/wfh_request_job_details.html', wfhreq=wfhreq, detail=detail)


@staff.route('/wfh/requests/approval')
@login_required
def show_wfh_requests_for_approval():
    approvers = StaffWorkFromHomeApprover.query.filter_by(approver_account_id=current_user.id).all()
    checkjob = StaffWorkFromHomeCheckedJob.query.all()
    return render_template('staff/wfh_requests_approval_info.html', approvers=approvers, checkjob=checkjob)


@staff.route('/wfh/requests/approval/pending/<int:req_id>')
@login_required
def pending_wfh_request_for_approval(req_id):
    req = StaffWorkFromHomeRequest.query.get(req_id)
    approver = StaffWorkFromHomeApprover.query.filter_by(account=current_user, requester=req.staff).first()
    return render_template('staff/wfh_request_pending_approval.html', req=req, approver=approver)


@staff.route('/wfh/requests/approve/<int:req_id>/<int:approver_id>')
@login_required
def wfh_approve(req_id, approver_id):
    approval = StaffWorkFromHomeApproval(
        request_id=req_id,
        approver_id=approver_id,
        is_approved=True,
        updated_at=tz.localize(datetime.today())
    )
    db.session.add(approval)
    db.session.commit()
    # approve_msg = u'การขออนุมัติWFH {} ได้รับการอนุมัติโดย {} เรียบร้อยแล้ว'.format(approval, current_user.personal_info.fullname)
    # line_bot_api.push_message(to=req.staff.line_id,messages=TextSendMessage(text=approve_msg))
    flash(u'อนุมัติขอทำงานที่บ้านให้บุคลากรในสังกัดเรียบร้อยแล้ว')
    return redirect(url_for('staff.show_wfh_requests_for_approval'))


@staff.route('/wfh/requests/reject/<int:req_id>/<int:approver_id>')
@login_required
def wfh_reject(req_id, approver_id):
    approval = StaffWorkFromHomeApproval(
        request_id=req_id,
        approver_id=approver_id,
        is_approved=False,
        updated_at=tz.localize(datetime.today())
    )
    db.session.add(approval)
    db.session.commit()
    # approve_msg = u'การขออนุมัติWFH {} ไม่ได้รับการอนุมัติ กรุณาติดต่อ {}'.format(approval, current_user.personal_info.fullname)
    # line_bot_api.push_message(to=req.staff.line_id,messages=TextSendMessage(text=approve_msg))
    flash(u'ไม่อนุมัติขอทำงานที่บ้านให้บุคลากรในสังกัดเรียบร้อยแล้ว')
    return redirect(url_for('staff.show_wfh_requests_for_approval'))


@staff.route('/wfh/requests/approved/list/<int:requester_id>')
@login_required
def show_wfh_approved_list_each_person(requester_id):
    requester = StaffWorkFromHomeRequest.query.filter_by(staff_account_id=requester_id)

    return render_template('staff/wfh_all_approved_list_each_person.html', requester=requester)


@staff.route('/wfh/requests/<int:request_id>/approvals')
@login_required
def show_wfh_approval(request_id):
    request = StaffWorkFromHomeRequest.query.get(request_id)
    approvers = StaffWorkFromHomeApprover.query.filter_by(staff_account_id=current_user.id)
    return render_template('staff/wfh_approval_status.html', request=request, approvers=approvers)


@staff.route('/wfh/<int:request_id>/info/edit-detail/<detail_id>',
             methods=['GET', 'POST'])
@login_required
def edit_wfh_job_detail(request_id, detail_id):
    detail = StaffWorkFromHomeJobDetail.query.get(detail_id)
    if request.method == 'POST':
        detail.activity = request.form.get('activity')
        db.session.add(detail)
        db.session.commit()
        return redirect(url_for('staff.wfh_show_request_info', request_id=request_id))

    detail = StaffWorkFromHomeJobDetail.query.get(detail_id)
    return render_template('staff/edit_wfh_job_detail.html', detail=detail, request_id=request_id)


@staff.route('/wfh/<int:request_id>/info/finish-job-detail/<detail_id>')
@login_required
def finish_wfh_job_detail(request_id, detail_id):
    detail = StaffWorkFromHomeJobDetail.query.get(detail_id)
    if detail:
        detail.status = True
        db.session.add(detail)
        db.session.commit()
        return redirect(url_for('staff.wfh_show_request_info', request_id=request_id))


@staff.route('/wfh/info/cancel-job-detail/<detail_id>')
@login_required
def cancel_wfh_job_detail(detail_id):
    detail = StaffWorkFromHomeJobDetail.query.get(detail_id)
    if detail:
        db.session.delete(detail)
        db.session.commit()
        return redirect(url_for('staff.wfh_show_request_info', request_id=detail.wfh_id))


@staff.route('/wfh/<int:request_id>/info/unfinish-job-detail/<detail_id>')
@login_required
def unfinish_wfh_job_detail(request_id, detail_id):
    detail = StaffWorkFromHomeJobDetail.query.get(detail_id)
    if detail:
        detail.status = False
        db.session.add(detail)
        db.session.commit()
        return redirect(url_for('staff.wfh_show_request_info', request_id=request_id))


@staff.route('/wfh/<int:request_id>/info/add-overall-result',
             methods=['GET', 'POST'])
@login_required
def add_overall_result_work_from_home(request_id):
    if request.method == 'POST':
        form = request.form
        result = StaffWorkFromHomeCheckedJob(
            overall_result=form.get('overall_result'),
            finished_at=tz.localize(datetime.today()),
            request_id=request_id
        )
        db.session.add(result)
        db.session.commit()
        wfhreq = StaffWorkFromHomeRequest.query.get(request_id)
        detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
        check = StaffWorkFromHomeCheckedJob.query.filter_by(request_id=request_id)
        return render_template('staff/wfh_record_info_each_request_subordinate.html',
                                        req=wfhreq, job_detail=detail, checkjob=check)

    else:
        wfhreq = StaffWorkFromHomeRequest.query.get(request_id)
        detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
        return render_template('staff/wfh_add_overall_result.html', wfhreq=wfhreq, detail=detail)


@staff.route('wfh/<int:request_id>/check/<int:check_id>',
                                    methods=['GET', 'POST'])
@login_required
def comment_wfh_request(request_id, check_id):
    checkjob = StaffWorkFromHomeCheckedJob.query.get(check_id)
    approval = StaffWorkFromHomeApproval.query.filter(and_(StaffWorkFromHomeApproval.request_id==request_id,
                                                StaffWorkFromHomeApproval.approver.has(account=current_user))).first()
    if request.method == 'POST':
        checkjob.id = check_id,
        if not approval.approval_comment:
            approval.approval_comment = request.form.get('approval_comment')
        else:
            approval.approval_comment += "," + request.form.get('approval_comment')
        approval.checked_at = tz.localize(datetime.today())
        db.session.add(checkjob)
        db.session.commit()
        return redirect(url_for('staff.show_wfh_requests_for_approval'))

    else:
        req = StaffWorkFromHomeRequest.query.get(request_id)
        job_detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
        check = StaffWorkFromHomeCheckedJob.query.filter_by(id=check_id)
        return render_template('staff/wfh_approval_comment.html', req=req, job_detail=job_detail,
                               checkjob=check)


@staff.route('wfh/<int:request_id>/record/info',
             methods=['GET', 'POST'])
@login_required
def record_each_request_wfh_request(request_id):
    req = StaffWorkFromHomeRequest.query.get(request_id)
    job_detail = StaffWorkFromHomeJobDetail.query.filter_by(wfh_id=request_id)
    check = StaffWorkFromHomeCheckedJob.query.filter_by(request_id=request_id)
    return render_template('staff/wfh_record_info_each_request.html', req=req, job_detail=job_detail,
                           checkjob=check)


@staff.route('/wfh/requests/list',
            methods=['GET', 'POST'])
@login_required
def wfh_requests_list():
    if request.method == 'POST':
        form = request.form
        start_dt, end_dt = form.get('dates').split(' - ')
        start_date = datetime.strptime(start_dt, '%m/%d/%Y')
        end_date = datetime.strptime(end_dt, '%m/%d/%Y')

        wfh_request = StaffWorkFromHomeRequest.query.filter(and_(StaffWorkFromHomeRequest.start_datetime >= start_date,
                                                     StaffWorkFromHomeRequest.end_datetime <= end_date))
        return render_template('staff/wfh_request_result_by_date.html', request=wfh_request,
                               start_date=start_date.date(), end_date=end_date.date() )
    else:
        return render_template('staff/wfh_request_info_by_date.html')


@staff.route('/for-hr')
@login_required
def for_hr():
    return render_template('staff/for_hr.html')