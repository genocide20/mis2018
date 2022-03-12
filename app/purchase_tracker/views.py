# -*- coding:utf-8 -*-
import requests, os
from flask import render_template, request, flash, redirect, url_for, send_from_directory
from flask_login import current_user, login_required
from flask_user import roles_required
from oauth2client.service_account import ServiceAccountCredentials
from pandas import DataFrame
from pydrive.auth import GoogleAuth
from werkzeug.utils import secure_filename
from . import purchase_tracker_bp as purchase_tracker
from .forms import *
from datetime import datetime, timedelta
from pytz import timezone
from pydrive.drive import GoogleDrive
from .models import PurchaseTrackerAccount
from flask_mail import Message
from ..main import mail

# Upload images for Google Drive


FOLDER_ID = "1JYkU2kRvbvGnmpQ1Tb-TcQS-vWQKbXvy"

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()

bangkok = timezone('Asia/Bangkok')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@purchase_tracker.route('/official/')
def landing_page():
    return render_template('purchase_tracker/first_page.html')


@purchase_tracker.route('/personnel/personnel_index')
def staff_index():
    return render_template('purchase_tracker/personnel/personnel_index.html')


@purchase_tracker.route('/main')
def index():
    return render_template('purchase_tracker/index.html')


@purchase_tracker.route('/create', methods=['GET', 'POST'])
@login_required
def add_account():
    form = CreateAccountForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            filename = ''
            purchase_tracker = PurchaseTrackerAccount()
            form.populate_obj(purchase_tracker)
            purchase_tracker.creation_date = bangkok.localize(datetime.now())
            purchase_tracker.staff = current_user
            drive = initialize_gdrive()
            if form.upload.data:
                if not filename or (form.upload.data.filename != filename):
                    upfile = form.upload.data
                    filename = secure_filename(upfile.filename)
                    upfile.save(filename)
                    file_drive = drive.CreateFile({'title': filename,
                                                   'parents': [{'id': FOLDER_ID, "kind": "drive#fileLink"}]})
                    file_drive.SetContentFile(filename)
                    try:
                        file_drive.Upload()
                        permission = file_drive.InsertPermission({'type': 'anyone',
                                                                  'value': 'anyone',
                                                                  'role': 'reader'})
                    except:
                        flash('Failed to upload the attached file to the Google drive.', 'danger')
                    else:
                        flash('The attached file has been uploaded to the Google drive', 'success')
                        purchase_tracker.url = file_drive['id']

            db.session.add(purchase_tracker)
            db.session.commit()
            flash(u'บันทึกข้อมูลสำเร็จ.', 'success')
            return render_template('purchase_tracker/personnel/personnel_index.html')
        # Check Error
        else:
            for er in form.errors:
                flash(er, 'danger')
    return render_template('purchase_tracker/create_account.html', form=form)


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scopes)
    return GoogleDrive(gauth)


@purchase_tracker.route('/track/')
@purchase_tracker.route('/track/<int:account_id>')
def track(account_id=None):
    if account_id is not None:
        from sqlalchemy import desc
        tracker = PurchaseTrackerAccount.query.get(account_id)
        trackers = PurchaseTrackerAccount.query.filter_by(staff_id=current_user.id).all()
        activities = [a.to_list() for a in PurchaseTrackerStatus.query.filter_by(account_id=account_id)
            .order_by(PurchaseTrackerStatus.start_date)]
        if not activities:
            default_date = datetime.now().isoformat()
        else:
            default_date = activities[-1][3]
        return render_template('purchase_tracker/tracking.html',
                               account_id=account_id,
                               tracker=tracker,
                               trackers=trackers,
                               desc=desc,
                               PurchaseTrackerStatus=PurchaseTrackerStatus,
                               activities=activities,
                               default_date=default_date)
    else:
        from sqlalchemy import desc
        tracker = PurchaseTrackerAccount.query.get(account_id)
        trackers = PurchaseTrackerAccount.query.filter_by(staff_id=current_user.id).all()
        activities = [a.to_list() for a in PurchaseTrackerStatus.query.filter_by(account_id=account_id)
            .order_by(PurchaseTrackerStatus.start_date)]
        if not activities:
            default_date = datetime.now().isoformat()
        else:
            default_date = activities[-1][3]
        return render_template('purchase_tracker/tracking.html',
                               account_id=account_id,
                               tracker=tracker,
                               trackers=trackers,
                               desc=desc,
                               PurchaseTrackerStatus=PurchaseTrackerStatus,
                               activities=activities,
                               default_date=default_date)


@purchase_tracker.route('/supplies')
# @roles_required('')
def supplies():
    from sqlalchemy import desc
    purchase_trackers = PurchaseTrackerAccount.query.all()
    return render_template('purchase_tracker/procedure_supplies.html',
                           purchase_trackers=purchase_trackers,
                           desc=desc,
                           PurchaseTrackerStatus=PurchaseTrackerStatus)


@purchase_tracker.route('/description')
def description():
    return render_template('purchase_tracker/description.html')


@purchase_tracker.route('/contact')
def contact():
    return render_template('purchase_tracker/contact_us.html')


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


@purchase_tracker.route('/account/<int:account_id>/update', methods=['GET', 'POST'])
@login_required
def update_status(account_id):
    form = StatusForm()
    tracker = PurchaseTrackerAccount.query.get(account_id)
    if request.method == 'POST':
        if form.validate_on_submit():
            status = PurchaseTrackerStatus()
            form.populate_obj(status)
            status.account_id = account_id
            status.status_date = bangkok.localize(datetime.now())
            status.creation_date = bangkok.localize(datetime.now())
            status.cancel_datetime = bangkok.localize(datetime.now())
            status.update_datetime = bangkok.localize(datetime.now())
            status.staff = current_user
            status.end_date = form.start_date.data + timedelta(days=int(form.days.data))
            # TODO: calculate end date from time needed to finish the task
            db.session.add(status)
            db.session.commit()
            title = u'แจ้งเตือนการปรับเปลี่ยนสถานะการจัดซื้อพัสดุและครุภัณฑ์หมายเลข {}'.format(status.account.number)
            message = u'เรียน {}\n\nสถานะการจัดซื้อพัสดุและครุภัณฑ์หมายเลข {} คือ {}'\
                .format(current_user.personal_info.fullname, status.account.number, status.activity)
            message += u'\n\n======================================================'
            message += u'\nอีเมลนี้ส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ ' \
                       u'หากมีปัญหาใดๆเกี่ยวกับเว็บไซต์กรุณาติดต่อหน่วยข้อมูลและสารสนเทศ '
            message += u'\nThis email was sent by an automated system. Please do not reply.' \
                       u' If you have any problem about website, please contact the IT unit.'
            send_mail([u'{}@mahidol.ac.th'.format(tracker.staff.email)], title, message)
            flash(u'อัพเดตข้อมูลเรียบร้อย', 'success')
        # Check Error
        else:
            for er in form.errors:
                flash(er, 'danger')
    activities = [a.to_list() for a in PurchaseTrackerStatus.query.filter_by(account_id=account_id)
        .order_by(PurchaseTrackerStatus.start_date)]
    if not activities:
        default_date = datetime.now().isoformat()
    else:
        default_date = activities[-1][3]
    return render_template('purchase_tracker/update_record.html',
                            account_id=account_id, form=form, activities=activities, tracker=tracker,
                           default_date=default_date)


@purchase_tracker.route('/account/<int:account_id>/status/<int:status_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_update_status(account_id, status_id):
    status = PurchaseTrackerStatus.query.get(status_id)
    form = StatusForm(obj=status)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(status)
            status.account_id = account_id
            status.status_date = bangkok.localize(datetime.now())
            status.creation_date = bangkok.localize(datetime.now())
            status.cancel_datetime = bangkok.localize(datetime.now())
            status.update_datetime = bangkok.localize(datetime.now())
            status.staff = current_user
            status.end_date = form.start_date.data + timedelta(days=int(form.days.data))
            db.session.add(status)
            db.session.commit()
            title = u'แจ้งเตือนการแก้ไขปรับเปลี่ยนสถานะการจัดซื้อพัสดุและครุภัณฑ์หมายเลข {}'.format(status.account.number)
            message = u'เรียน {}\n\nสถานะการจัดซื้อพัสดุและครุภัณฑ์หมายเลข {} คือ {}' \
                .format(current_user.personal_info.fullname, status.account.number, status.activity)
            message += u'\n\n======================================================'
            message += u'\nอีเมลนี้ส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ ' \
                       u'หากมีปัญหาใดๆเกี่ยวกับเว็บไซต์กรุณาติดต่อหน่วยข้อมูลและสารสนเทศ '
            message += u'\nThis email was sent by an automated system. Please do not reply.' \
                       u' If you have any problem about website, please contact the IT unit.'
            send_mail([u'{}@mahidol.ac.th'.format(status.account.staff.email)], title, message)
            flash(u'แก้ไขข้อมูลเรียบร้อย', 'success')
        return redirect(url_for('purchase_tracker.update_status', status_id=status.id, account_id=account_id))
    return render_template('purchase_tracker/edit_update_record.html',
                                account_id=account_id, form=form)


@purchase_tracker.route('/account/<int:account_id>/status/<int:status_id>/delete')
@login_required
def delete_update_status(account_id, status_id):
    if account_id:
        status = PurchaseTrackerStatus.query.get(status_id)
        flash(u'Information has been removed from the update status.')
        db.session.delete(status)
        db.session.commit()
        return redirect(url_for('purchase_tracker.update_status', account_id=account_id))


@purchase_tracker.route('/account/update_status/info/download')
@login_required
def update_status_info_download():
    trackers = PurchaseTrackerAccount.query.filter_by(staff_id=current_user.id).all()
    records = []
    for account in trackers:
        for record in account.records:
            delta = record.end_date-record.start_date
            records.append({
                'account_id': u"{}".format(account.id),
                'number': u"{}".format(account.number),
                'booking_date': u"{}".format(account.booking_date),
                'subject': u"{}".format(account.subject),
                'amount': u"{}".format(account.amount),
                'formats': u"{}".format(account.formats),
                'activity': u"{}".format(record.activity),
                'staff': u"{}".format(record.staff.personal_info.fullname),
                'start_date': u"{}".format(record.start_date),
                'end_date': u"{}".format(record.end_date),
                'comment': u"{}".format(record.comment),
                'days': u"{}".format(delta.days),
                    })
    df = DataFrame(records)
    df.to_excel('account_summary.xlsx')
    return send_from_directory(os.getcwd(), filename='account_summary.xlsx')
