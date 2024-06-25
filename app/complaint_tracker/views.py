# -*- coding:utf-8 -*-
from datetime import datetime
import os
import arrow
import requests
from flask import render_template, flash, redirect, url_for, request, make_response, jsonify, current_app
from flask_login import current_user
from flask_login import login_required
from pytz import timezone
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from app.auth.views import line_bot_api
from werkzeug.utils import secure_filename
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive
from app.complaint_tracker import complaint_tracker
from app.complaint_tracker.forms import (create_record_form, ComplaintActionRecordForm, ComplaintInvestigatorForm,
                                         ComplaintPerformanceReportForm, ComplaintCoordinatorForm)
from app.complaint_tracker.models import *
from app.main import mail
from ..main import csrf
from flask_mail import Message

from ..procurement.models import ProcurementDetail

gauth = GoogleAuth()
keyfile_dict = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()
scopes = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scopes)
drive = GoogleDrive(gauth)

localtz = timezone('Asia/Bangkok')

FOLDER_ID = '1832el0EAqQ6NVz2wB7Ade6wRe-PsHQsu'

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scopes)
    return GoogleDrive(gauth)


@complaint_tracker.route('/')
def index():
    categories = ComplaintCategory.query.all()
    return render_template('complaint_tracker/index.html', categories=categories)


@complaint_tracker.route('/issue/<int:topic_id>', methods=['GET', 'POST'])
def new_record(topic_id, room=None, procurement=None):
    topic = ComplaintTopic.query.get(topic_id)
    ComplaintRecordForm = create_record_form(record_id=None)
    form = ComplaintRecordForm()
    room_number = request.args.get('number')
    location = request.args.get('location')
    procurement_no = request.args.get('procurement_no')
    admins = []
    for a in topic.admins:
        if a.admin == current_user:
            admins.append(a)
    if room_number and location:
        room = RoomResource.query.filter_by(number=room_number, location=location).first()
    if procurement_no:
        procurement = ProcurementDetail.query.filter_by(procurement_no=procurement_no).first()
    if form.validate_on_submit():
        record = ComplaintRecord()
        form.populate_obj(record)
        file = form.file_upload.data
        record.topic = topic
        if current_user.is_authenticated:
            record.complainant = current_user
        drive = initialize_gdrive()
        if file:
            file_name = secure_filename(file.filename)
            file.save(file_name)
            file_drive = drive.CreateFile({'title': file_name,
                                           'parents': [{'id': FOLDER_ID, "kind": "drive#fileLink"}]})
            file_drive.SetContentFile(file_name)
            file_drive.Upload()
            permission = file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
            record.url = file_drive['id']
            record.file_name = file_name
        if topic.code == 'room' and room:
            record.rooms.append(room)
            db.session.add(record)
        if topic.code == 'runied' and procurement:
            record.procurements.append(procurement)
            db.session.add(record)
        if (((form.is_contact.data and form.fl_name.data and (form.telephone.data or form.email.data)) or
            (not form.is_contact.data and (form.fl_name.data or form.telephone.data or form.email.data))) or
                (not form.is_contact.data and not form.fl_name.data and not form.telephone.data and not form.email.data)):
            db.session.add(record)
            db.session.commit()
            flash('รับเรื่องแจ้งเรียบร้อย', 'success')
            create_at = arrow.get(record.created_at, 'Asia/Bangkok').datetime
            complaint_link = url_for("comp_tracker.edit_record_admin", record_id=record.id, _external=True)
            msg = ('มีการแจ้งเรื่องในส่วนของ{} หัวข้อ{}' \
                  '\nเวลาแจ้ง : วันที่ {} เวลา {}' \
                  '\nซึ่งมีรายละเอียด ดังนี้ {}' \
                  '\nคลิกที่ Link เพื่อดำเนินการ {}'.format(topic.category, topic.topic,
                                                            create_at.astimezone(localtz).strftime('%d/%m/%Y'),
                                                            create_at.astimezone(localtz).strftime('%H:%M'),
                                                            form.desc.data,
                                                            complaint_link)
                  )
            if not current_app.debug:
                try:
                    line_bot_api.push_message(to=[a.admin.line_id for a in topic.admins if a.is_supervisor == False],
                                              messages=TextSendMessage(text=msg))
                except LineBotApiError:
                    pass
            if current_user.is_authenticated:
                return redirect(url_for('comp_tracker.complainant_index'))
            else:
                return redirect(url_for('comp_tracker.closing_page'))
        else:
            flash('กรุณากรอกชื่อ-นามสกุล และเบอร์โทรศัพท์ หรืออีเมล', 'danger')
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('complaint_tracker/record_form.html', form=form, topic=topic, room=room,
                           admins=admins, procurement=procurement)


@complaint_tracker.route('issue/closing-page')
def closing_page():
    return render_template('complaint_tracker/closing.html')


@complaint_tracker.route('/issue/records/<int:record_id>', methods=['GET', 'POST', 'PATCH'])
@login_required
def edit_record_admin(record_id):
    record = ComplaintRecord.query.get(record_id)
    admins = []
    investigators = []
    coordinators = []
    for a in record.topic.admins:
        if a.admin == current_user:
            admins.append(a)
    for i in record.investigators:
        if i.admin.admin == current_user:
            investigators.append(i)
    for c in record.coordinators:
        if c.coordinator == current_user:
            coordinators.append(c)
    ComplaintRecordForm = create_record_form(record_id)
    form = ComplaintRecordForm(obj=record)
    form.deadline.data = form.deadline.data.astimezone(localtz) if form.deadline.data else None
    if record.url:
        file_upload = drive.CreateFile({'id': record.url})
        file_upload.FetchMetadata()
        file_url = file_upload.get('embedLink')
    else:
        file_url = None
    if request.method == 'PATCH':
        if record.closed_at is None:
            record.closed_at = arrow.now('Asia/Bangkok').datetime
            flash('ปิดรายการเรียบร้อย', 'success')
        else:
            record.closed_at = None
            flash('เปิดรายการอีกครั้งเรียบร้อย', 'success')
        db.session.add(record)
        db.session.commit()
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    if form.validate_on_submit():
        form.populate_obj(record)
        record.deadline = arrow.get(form.deadline.data, 'Asia/Bangkok').datetime if form.deadline.data else None
        db.session.add(record)
        db.session.commit()
        flash(u'บันทึกข้อมูลเรียบร้อย', 'success')
        if record.priority is not None and record.priority.priority == 2:
            complaint_link = url_for("comp_tracker.edit_record_admin", record_id=record_id, _external=True)
            create_at = arrow.get(record.created_at, 'Asia/Bangkok').datetime
            msg = ('มีการแจ้งเรื่องในส่วนของ{} หัวข้อ{}' \
                   '\nเวลาแจ้ง : วันที่ {} เวลา {}' \
                   '\nซึ่งมีรายละเอียด ดังนี้ {}' \
                   '\nคลิกที่ Link เพื่อดำเนินการ {}'.format(record.topic.category, record.topic,
                                                             create_at.astimezone(localtz).strftime('%d/%m/%Y'),
                                                             create_at.astimezone(localtz).strftime('%H:%M'),
                                                             record.desc, complaint_link)
                )
            if not current_app.debug:
                try:
                    line_bot_api.push_message(to=[a.admin.line_id for a in record.topic.admins if a.is_supervisor == True],
                                              messages=TextSendMessage(text=msg))
                except LineBotApiError:
                    pass
        else:
            pass
    return render_template('complaint_tracker/admin_record_form.html', form=form, record=record,
                           file_url=file_url, admins=admins, investigators=investigators, coordinators=coordinators)


@complaint_tracker.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_index():
    tab = request.args.get('tab')
    query = ComplaintRecord.query.all()
    complaint_news = []
    complaint_pending = []
    complaint_progress = []
    complaint_completed = []
    for record in query:
        if record.status is not None:
            if record.status.code == 'pending':
                complaint_pending.append(record)
            elif record.status.code == 'progress':
                complaint_progress.append(record)
            elif record.status.code == 'completed':
                complaint_completed.append(record)
        else:
            complaint_news.append(record)
    records = complaint_pending if tab == 'pending' else complaint_progress if tab == 'progress' \
        else complaint_completed if tab == 'completed' else complaint_news
    return render_template('complaint_tracker/admin_index.html', records=records, tab=tab)


@complaint_tracker.route('/topics/<code>')
def scan_qr_code_room(code):
    topic = ComplaintTopic.query.filter_by(code=code).first()
    return redirect(url_for('comp_tracker.new_record', topic_id=topic.id, **request.args))


@complaint_tracker.route('/scan-qrcode/complaint/<code>')
@csrf.exempt
def scan_qr_code_complaint(code):
    topic = ComplaintTopic.query.filter_by(code=code).first()
    return render_template('complaint_tracker/qr_code_scan_to_complaint.html', topic=topic.id)


@complaint_tracker.route('/issue/comment/add/<int:record_id>', methods=['GET', 'POST'])
@complaint_tracker.route('/issue/comment/edit/<int:action_id>', methods=['GET', 'POST'])
def edit_comment(record_id=None, action_id=None):
    if record_id:
        record = ComplaintRecord.query.get(record_id)
        admin = ComplaintAdmin.query.filter_by(admin=current_user, topic=record.topic).first()
        if not admin:
            misc_topic = ComplaintTopic.query.filter_by(code='misc').first()
            admin = ComplaintAdmin.query.filter_by(admin=current_user, topic=misc_topic).first()
        form = ComplaintActionRecordForm()
    elif action_id:
        action = ComplaintActionRecord.query.get(action_id)
        form = ComplaintActionRecordForm(obj=action)
    if form.validate_on_submit():
        if record_id:
            action = ComplaintActionRecord()
        form.populate_obj(action)
        if record_id:
            action.record_id = record_id
            action.reviewer_id = admin.id
        action.comment_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(action)
        db.session.commit()
        if record_id:
            flash('เพิ่มความคิดเห็น/ข้อเสนอแนะสำเร็จ', 'success')
            resp = make_response(render_template('complaint_tracker/comment_template.html', action=action))
            resp.headers['HX-Trigger'] = 'closeModal'
        else:
            flash('แก้ไขความคิดเห็น/ข้อเสนอแนะสำเร็จ', 'success')
            resp = make_response()
            resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('complaint_tracker/modal/comment_record_modal.html', record_id=record_id,
                           action_id=action_id, form=form)


@complaint_tracker.route('/issue/comment/delete/<int:action_id>', methods=['GET', 'DELETE'])
def delete_comment(action_id):
    if request.method == 'DELETE':
        action = ComplaintActionRecord.query.get(action_id)
        db.session.delete(action)
        db.session.commit()
        flash('ลบความคิดเห็น/ข้อเสนอแนะสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp


@complaint_tracker.route('/issue/invite/add/<int:record_id>', methods=['GET', 'POST'])
@complaint_tracker.route('/issue/invite/delete/<int:investigator_id>', methods=['GET', 'DELETE'])
def add_invite(record_id=None, investigator_id=None):
    form = ComplaintInvestigatorForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            invites = []
            for admin_id in form.invites.data:
                investigator = ComplaintInvestigator(inviter_id=current_user.id, admin_id=admin_id.id, record_id=record_id)
                db.session.add(investigator)
                invites.append(investigator)
            db.session.commit()
            record = ComplaintRecord.query.get(record_id)
            create_at = arrow.get(record.created_at, 'Asia/Bangkok').datetime
            complaint_link = url_for('comp_tracker.edit_record_admin', record_id=record_id, _external=True)
            msg = ('มีการแจ้งเรื่องในส่วนของ{} หัวข้อ{}' \
                  '\nเวลาแจ้ง : วันที่ {} เวลา {}' \
                  '\nซึ่งมีรายละเอียด ดังนี้ {}'
                  '\nคลิกที่ Link เพื่อดำเนินการ {}'.format(record.topic.category, record.topic.topic,
                                                            create_at.astimezone(localtz).strftime('%d/%m/%Y'),
                                                            create_at.astimezone(localtz).strftime('%H:%M'),
                                                            record.desc, complaint_link))
            title = f'''แจ้งปัญหาร้องเรียนในส่วนของ{record.topic.category}'''
            message = f'''มีการแจ้งปัญหาร้องเรียนมาในเรื่องของ{record.topic} โดยมีรายละเอียดปัญหาที่พบ ได้แก่ {record.desc}\n\n'''
            message += f'''กรุณาดำเนินการแก้ไขปัญหาตามที่ได้รับแจ้งจากผู้ใช้งาน\n\n\n'''
            message += f'''ลิงค์สำหรับจัดการข้อร้องเรียน : {complaint_link}'''
            send_mail([invite.admin.admin.email + '@mahidol.ac.th' for invite in invites], title, message)
            if not current_app.debug:
                try:
                    line_bot_api.push_message(to=[invite.admin.admin.line_id for invite in invites],
                                              messages=TextSendMessage(text=msg))
                except LineBotApiError:
                    pass
            flash('เพิ่มรายชื่อผู้เกี่ยวข้องสำเร็จ', 'success')
            resp = make_response(render_template('complaint_tracker/invite_template.html', invites=invites))
            resp.headers['HX-Trigger'] = 'closePopup'
            return resp
    elif request.method == 'DELETE':
        investigator = ComplaintInvestigator.query.get(investigator_id)
        db.session.delete(investigator)
        db.session.commit()
        flash('ลบรายชื่อผู้เกี่ยวข้องสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('complaint_tracker/modal/invite_record_modal.html', record_id=record_id,
                           form=form)


@complaint_tracker.route('/complaint/user', methods=['GET'])
@login_required
def complainant_index():
    record_list = []
    records = ComplaintRecord.query.filter_by(complainant=current_user).all()
    for record in records:
        if record.url:
            file_upload = drive.CreateFile({'id': record.url})
            file_upload.FetchMetadata()
            record.url = file_upload.get('embedLink')
        else:
            record.url = None
        record_list.append(record)
    return render_template('complaint_tracker/complainant_index.html', record_list=record_list)


@complaint_tracker.route('/api/priority')
@login_required
def check_priority():
    priority_id = request.args.get('priorityID')
    priority = ComplaintPriority.query.get(priority_id)
    template = f'<span class="tag is-light">{priority.priority_detail}</span>'
    template += f'<span id="priority" class="tags"></span>'
    resp = make_response(template)
    return resp


@complaint_tracker.route('/issue/report/add/<int:record_id>', methods=['GET', 'POST'])
@complaint_tracker.route('/issue/report/edit/<int:report_id>', methods=['GET', 'POST'])
def create_report(record_id=None, report_id=None):
    if record_id:
        record = ComplaintRecord.query.get(record_id)
        admin = ComplaintAdmin.query.filter_by(admin=current_user, topic=record.topic).first()
        if not admin:
            misc_topic = ComplaintTopic.query.filter_by(code='misc').first()
            admin = ComplaintAdmin.query.filter_by(admin=current_user, topic=misc_topic).first()
        form = ComplaintPerformanceReportForm()
    elif report_id:
        report = ComplaintPerformanceReport.query.get(report_id)
        form = ComplaintPerformanceReportForm(obj=report)
    if form.validate_on_submit():
        if record_id:
            report = ComplaintPerformanceReport()
        form.populate_obj(report)
        if record_id:
            report.record_id = record_id
            report.reporter_id = admin.id
        report.report_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(report)
        db.session.commit()
        if record_id:
            flash('เพิ่มรายงานผลการดำเนินงานสำเร็จ', 'success')
            resp = make_response(render_template('complaint_tracker/performance_report_template.html',
                                                 report=report))
            resp.headers['HX-Trigger'] = 'closeReport'
        else:
            flash('แก้ไขรายงานผลการดำเนินงานสำเร็จ', 'success')
            resp = make_response()
            resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('complaint_tracker/modal/performance_report_modal.html', record_id=record_id,
                           report_id=report_id, form=form)


@complaint_tracker.route('/issue/report/delete/<int:report_id>', methods=['GET', 'DELETE'])
def delete_report(report_id):
    if request.method == 'DELETE':
        report = ComplaintPerformanceReport.query.get(report_id)
        db.session.delete(report)
        db.session.commit()
        flash('ลบรายงานผลการดำเนินงานสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp


@complaint_tracker.route('/issue/coordinator/add/<int:record_id>', methods=['GET', 'POST'])
@complaint_tracker.route('/issue/coordinator/delete/<int:coordinator_id>', methods=['GET', 'DELETE'])
def add_coordinator(record_id=None, coordinator_id=None):
    form = ComplaintCoordinatorForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            coordinators = []
            for coordinator_id in form.coordinators.data:
                coordinator = ComplaintCoordinator(coordinator_id=coordinator_id.id, record_id=record_id,
                                                   recorder_id=current_user.id)
                db.session.add(coordinator)
                coordinators.append(coordinator)
            db.session.commit()
            record = ComplaintRecord.query.get(record_id)
            complaint_link = url_for('comp_tracker.edit_record_admin', record_id=record_id, _external=True)
            title = f'''แจ้งปัญหาร้องเรียนในส่วนของ{record.topic.category}'''
            message = f'''มีการแจ้งปัญหาร้องเรียนมาในเรื่องของ{record.topic} โดยมีรายละเอียดปัญหาที่พบ ได้แก่ {record.desc}\n\n'''
            message += f'''กรุณาดำเนินการแก้ไขปัญหาตามที่ได้รับแจ้งจากผู้ใช้งาน\n\n\n'''
            message += f'''ลิงค์สำหรับจัดการข้อร้องเรียน : {complaint_link}'''
            send_mail([coordinator.coordinator.email + '@mahidol.ac.th' for coordinator in coordinators], title, message)
            flash('เพิ่มรายชื่อผูประสานงานสำเร็จ', 'success')
            resp = make_response(render_template('complaint_tracker/coordinator_template.html',
                                                 coordinators=coordinators))
            resp.headers['HX-Trigger'] = 'closeCoordinator'
            return resp
    elif request.method == 'DELETE':
        coordinator = ComplaintCoordinator.query.get(coordinator_id)
        db.session.delete(coordinator)
        db.session.commit()
        flash('ลบรายชื่อผูประสานงานสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('complaint_tracker/modal/coordinator_modal.html', record_id=record_id,
                           form=form)


@complaint_tracker.route('/issue/record/coordinator/complaint-acknowledgment/<int:coordinator_id>', methods=['GET', 'POST'])
def acknowledge_complaint(coordinator_id):
    if request.method == 'POST':
        coordinator = ComplaintCoordinator.query.get(coordinator_id)
        coordinator.received_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(coordinator)
        db.session.commit()
        flash('ยืนยันเรียบร้อย', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp


@complaint_tracker.route('/issue/record/coordinator/note/add/<int:coordinator_id>', methods=['GET', 'POST'])
@login_required
def edit_note(coordinator_id):
    coordinator = ComplaintCoordinator.query.get(coordinator_id)
    form = ComplaintCoordinatorForm(obj=coordinator)
    if request.method == 'GET':
        template = '''
            <tr>
                <td style="width: 100%;">
                    <label class="label">รายงานผลการดำเนินงาน</label>{}
                </td>
                <td>
                    <a class="button is-success is-outlined"
                        hx-post="{}" hx-include="closest tr">
                        <span class="icon"><i class="fas fa-save"></i></span>
                    </a>
                </td>
            </tr>
            '''.format(form.note(class_="textarea"),
                       url_for('comp_tracker.edit_note', coordinator_id=coordinator.id)
                       )
    if request.method == 'POST':
        coordinator.note = request.form.get('note')
        db.session.add(coordinator)
        db.session.commit()
        flash('บันทึกรายงานผลการดำเนินงานสำเร็จ', 'success')
        template = '''
            <tr>
                <td style="width: 100%;">
                    <label class="label">รายงานผลการดำเนินงาน</label>
                    <p class="notification">{}</p>
                </td>
                <td>
                    <div class="field has-addons">
                        <div class="control">
                            <a class="button is-light is-outlined"
                               hx-get="{}">
                                <span class="icon">
                                   <i class="fas fa-pencil has-text-dark"></i>
                                </span>
                                <span class="has-text-dark">ร่าง</span>
                            </a>
                        </div>
                        <div class="control">
                            <a class="button is-light is-outlined"
                                style="width: 5em"
                                hx-patch="{}"
                                hx-confirm="ท่านต้องการส่งรายงานผลการดำเนินงานหรือไม่">
                                <span class="icon">
                                    <i class="fas fa-paper-plane has-text-info"></i>
                                </span>
                                <span class="has-text-info">ส่ง</span>
                            </a>
                        </div>
                    </div>
                </td>
            </tr>
            '''.format(coordinator.note, url_for('comp_tracker.edit_note', coordinator_id=coordinator.id),
                       url_for('comp_tracker.submit_note', coordinator_id=coordinator.id))
    resp = make_response(template)
    return resp


@complaint_tracker.route('/issue/record/coordinator/note/note-submission/<int:coordinator_id>', methods=['GET', 'PATCH'])
@login_required
def submit_note(coordinator_id):
    coordinator = ComplaintCoordinator.query.get(coordinator_id)
    if request.method == 'PATCH':
        coordinator.submitted_datetime = arrow.now('Asia/Bangkok').datetime
        flash('ปิดรายงานผลการดำเนินงานเรียบร้อย', 'success')
        db.session.add(coordinator)
        db.session.commit()
    resp = make_response()
    resp.headers['HX-Refresh'] = 'true'
    return resp


@complaint_tracker.route('/issue/complainant/email-sending/<int:record_id>', methods=['GET', 'POST'])
def send_email(record_id):
    record = ComplaintRecord.query.get(record_id)
    form = request.form
    if request.method == 'POST':
        title = f'''{form.get('title')}'''
        message = f'''{form.get('detail')}'''
        send_mail([record.email], title, message)
        flash('ส่งอีเมลเรียบร้อย', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('complaint_tracker/modal/send_email_modal.html', record_id=record_id)


@complaint_tracker.route('/issue/report/assignee/add/<int:record_id>/<int:assignee_id>', methods=['GET', 'POST', 'DELETE'])
def edit_assignee(record_id, assignee_id):
    if request.method == 'POST':
        assignees = ComplaintAssignee(assignee_id=assignee_id, record_id=record_id,
                                      assignee_datetime=arrow.now('Asia/Bangkok').datetime)
        db.session.add(assignees)
        db.session.commit()
        flash('มอบหมายงานสำเร็จ', 'success')
        complaint_link = url_for('comp_tracker.edit_record_admin', record_id=record_id, _external=True)
        msg = ('ท่านได้รับมอบหมายให้ดำเนินการแก้ไขปัญหา'
               '\nกรุณาคลิกที่ Link เพื่อดำเนินการ {}'.format(complaint_link))
        if not current_app.debug:
            try:
                line_bot_api.push_message(to=[assignees.assignee.admin.line_id],
                                          messages=TextSendMessage(text=msg))
            except LineBotApiError:
                pass
    elif request.method == 'DELETE':
        assignee = ComplaintAssignee.query.filter_by(assignee_id=assignee_id, record_id=record_id).first()
        db.session.delete(assignee)
        db.session.commit()
        flash('ยกเลิกการมอบหมายงานสำเร็จ', 'success')
    resp = make_response()
    resp.headers['HX-Refresh'] = 'true'
    return resp