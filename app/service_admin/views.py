import os
import arrow
import requests
import pandas
from io import BytesIO
from pytz import timezone
from datetime import datetime, date

from app.academic_services.forms import create_request_form
from app.service_admin import service_admin
from app.academic_services.models import *
from flask import render_template, flash, redirect, url_for, request, session, make_response, jsonify, current_app, \
    send_file
from flask_login import current_user, login_required
from sqlalchemy import or_, and_
from app.service_admin.forms import (ServiceCustomerInfoForm, ServiceCustomerAddressForm, ServiceResultForm)
from app.main import app, get_credential, json_keyfile
from app.main import mail
from flask_mail import Message
from werkzeug.utils import secure_filename
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, TableStyle, Table, Spacer, KeepTogether, PageBreak

localtz = timezone('Asia/Bangkok')

sarabun_font = TTFont('Sarabun', 'app/static/fonts/THSarabunNew.ttf')
pdfmetrics.registerFont(sarabun_font)
style_sheet = getSampleStyleSheet()
style_sheet.add(ParagraphStyle(name='ThaiStyle', fontName='Sarabun'))
style_sheet.add(ParagraphStyle(name='ThaiStyleNumber', fontName='Sarabun', alignment=TA_RIGHT))
style_sheet.add(ParagraphStyle(name='ThaiStyleCenter', fontName='Sarabun', alignment=TA_CENTER))

gauth = GoogleAuth()
keyfile_dict = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()
scopes = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scopes)
drive = GoogleDrive(gauth)

FOLDER_ID = '1832el0EAqQ6NVz2wB7Ade6wRe-PsHQsu'

keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile, scopes)
    return GoogleDrive(gauth)


@service_admin.route('/')
# @login_required
def index():
    return render_template('service_admin/index.html')


@service_admin.route('/customer/view')
@login_required
def view_customer():
    customers = ServiceCustomerInfo.query.all()
    admin = ServiceAdmin.query.filter_by(admin_id=current_user.id).all()
    return render_template('service_admin/view_customer.html', customers=customers, admin=admin)


@service_admin.route('/customer/add', methods=['GET', 'POST'])
@service_admin.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def create_customer(customer_id=None):
    if customer_id:
        customer = ServiceCustomerInfo.query.get(customer_id)
        form = ServiceCustomerInfoForm(obj=customer)
    else:
        form = ServiceCustomerInfoForm()
    if form.validate_on_submit():
        if customer_id is None:
            customer = ServiceCustomerInfo()
        form.populate_obj(customer)
        if customer_id is None:
            customer.creator_id = current_user.id
            account = ServiceCustomerAccount(email=form.email.data, customer_info=customer)
        else:
            for account in customer.accounts:
                account.email = form.email.data
        db.session.add(account)
        db.session.add(customer)
        db.session.commit()
        if customer_id:
            flash('แก้ไขข้อมูลสำเร็จ', 'success')
        else:
            flash('เพิ่มลูกค้าสำเร็จ', 'success')
        return redirect(url_for('service_admin.view_customer'))
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('service_admin/create_customer.html', customer_id=customer_id,
                           form=form)


@service_admin.route('/customer/address/edit/<int:customer_id>', methods=['GET', 'POST'])
def create_address(customer_id=None):
    if customer_id:
        customer = ServiceCustomerInfo.query.get(customer_id)
        form = ServiceCustomerInfoForm(obj=customer)
    else:
        form = ServiceCustomerInfoForm()
    if form.validate_on_submit():
        if customer_id is None:
            customer = ServiceCustomerInfo()
        form.populate_obj(customer)
        if customer_id is None:
            customer.creator_id = current_user.id
        db.session.add(customer)
        db.session.commit()
        if customer_id:
            flash('แก้ไขข้อมูลสำเร็จ', 'success')
        else:
            flash('เพิ่มลูกค้าสำเร็จ', 'success')
        return redirect(url_for('service_admin.view_customer'))
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('service_admin/create_customer.html', customer_id=customer_id, form=form)


@service_admin.route('/request/index')
@login_required
def request_index():
    return render_template('service_admin/request_index.html')


@service_admin.route('/api/request/index')
def get_requests():
    admin = ServiceAdmin.query.filter_by(admin_id=current_user.id).all()
    labs = []
    sub_labs = []
    for a in admin:
        if a.lab:
            labs.append(a.lab.code)
        else:
            sub_labs.append(a.sub_lab.code)
    query = ServiceRequest.query.filter(or_(ServiceRequest.admin.has(id=current_user.id), ServiceRequest.lab.in_(labs))) \
        if labs else ServiceRequest.query.filter(or_(ServiceRequest.admin.has(id=current_user.id), ServiceRequest.lab.in_(sub_labs)))
    records_total = query.count()
    search = request.args.get('search[value]')
    if search:
        query = query.filter(ServiceRequest.created_at.contains(search))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        data.append(item_data)
    return jsonify({'data': data,
                    'recordFiltered': total_filtered,
                    'recordTotal': records_total,
                    'draw': request.args.get('draw', type=int)
                    })


@service_admin.route('/request/add/<int:customer_account_id>', methods=['GET'])
@service_admin.route('/request/edit/<int:request_id>', methods=['GET'])
@login_required
def create_request(request_id=None, customer_account_id=None):
    code = request.args.get('code')
    return render_template('service_admin/create_request.html', code=code, request_id=request_id, customer_account_id=customer_account_id)


@service_admin.route('/api/request/form', methods=['GET'])
def get_request_form():
    code = request.args.get('code')
    request_id = request.args.get('request_id')
    service_request = ServiceRequest.query.get(request_id)
    lab = ServiceLab.query.filter_by(code=code).first() if code else ServiceLab.query.filter_by(code=service_request.lab).first()
    sub_lab = ServiceSubLab.query.filter_by(code=code).first() if code else ServiceSubLab.query.filter_by(code=service_request.lab).first()
    sheetid = '1EHp31acE3N1NP5gjKgY-9uBajL1FkQe7CCrAu-TKep4'
    print('Authorizing with Google..')
    gc = get_credential(json_keyfile)
    wks = gc.open_by_key(sheetid)
    if sub_lab:
        sheet = wks.worksheet(sub_lab.sheet)
    else:
        sheet = wks.worksheet(lab.sheet)
    df = pandas.DataFrame(sheet.get_all_records())
    if request_id:
        data = service_request.data
        form = create_request_form(df)(**data)
    else:
        form = create_request_form(df)()
    template = ''
    for f in form:
        template += str(f)
    return template


def form_data(data):
    if isinstance(data, dict):
        return {k: form_data(v) for k, v in data.items() if k != "csrf_token" and k != 'submit'}
    elif isinstance(data, list):
        return [form_data(item) for item in data]
    elif isinstance(data, (date)):
        return data.isoformat()
    return data


@service_admin.route('/submit-request/add/<int:customer_account_id>', methods=['POST'])
@service_admin.route('/submit-request/edit/<int:request_id>', methods=['POST'])
def submit_request(request_id=None, customer_account_id=None):
    if request_id:
        service_request = ServiceRequest.query.get(request_id)
        lab = ServiceLab.query.filter_by(code=service_request.lab).first()
        sub_lab = ServiceSubLab.query.filter_by(code=service_request.lab).first()
    else:
        code = request.args.get('code')
        lab = ServiceLab.query.filter_by(code=code).first()
        sub_lab = ServiceSubLab.query.filter_by(code=code).first()
    sheetid = '1EHp31acE3N1NP5gjKgY-9uBajL1FkQe7CCrAu-TKep4'
    gc = get_credential(json_keyfile)
    wks = gc.open_by_key(sheetid)
    if sub_lab:
        sheet = wks.worksheet(sub_lab.sheet)
    else:
        sheet = wks.worksheet(lab.sheet)
    df = pandas.DataFrame(sheet.get_all_records())
    form = create_request_form(df)(request.form)
    if request_id:
        service_request.data = form_data(form.data)
        service_request.modified_at = arrow.now('Asia/Bangkok').datetime
    else:
        service_request = ServiceRequest(admin_id=current_user.id, customer_account_id=customer_account_id,
                                         created_at=arrow.now('Asia/Bangkok').datetime, lab=sub_lab.code if sub_lab
            else lab.code, data=form_data(form.data))
    db.session.add(service_request)
    db.session.commit()
    if not request_id:
        service_request.request_no = f'RQ{service_request.id}'
        db.session.add(service_request)
        db.session.commit()
    return redirect(url_for('service_admin.view_request', request_id=service_request.id))


@service_admin.route('/request/test/confirm/<int:request_id>', methods=['GET'])
def confirm_test(request_id):
    service_request = ServiceRequest.query.get(request_id)
    service_request.status = 'กำลังเริ่มการทดสอบ'
    db.session.add(service_request)
    db.session.commit()
    flash('เปลี่ยนสถานะสำเร็จ', 'success')
    return redirect(url_for('service_admin.request_index'))


@service_admin.route('/request/view/<int:request_id>')
@login_required
def view_request(request_id=None):
    service_request = ServiceRequest.query.get(request_id)
    return render_template('service_admin/view_request.html', service_request=service_request)


def generate_request_pdf(service_request, sign=False, cancel=False):
    logo = Image('app/static/img/logo-MU_black-white-2-1.png', 40, 40)

    sheetid = '1EHp31acE3N1NP5gjKgY-9uBajL1FkQe7CCrAu-TKep4'
    gc = get_credential(json_keyfile)
    wks = gc.open_by_key(sheetid)
    lab = ServiceLab.query.filter_by(code=service_request.lab).first()
    sub_lab = ServiceSubLab.query.filter_by(code=service_request.lab).first()
    if sub_lab:
        sheet = wks.worksheet(sub_lab.sheet)
    else:
        sheet = wks.worksheet(lab.sheet)
    df = pandas.DataFrame(sheet.get_all_records())
    data = service_request.data
    form = create_request_form(df)(**data)
    values = []
    set_fields = set()
    for fn in df.fieldGroup:
        for field in getattr(form, fn):
            if field.type == 'FieldList':
                for fd in field:
                    for f in fd:
                        if f.data != None and f.data != '' and f.data != [] and f.label not in set_fields:
                            set_fields.add(f.label)
                            if f.type == 'CheckboxField':
                                values.append(f"{f. label.text} : {', '.join(f.data)}")
                            else:
                                values.append(f"{f.label.text} : {f.data}")
            else:
                if field.data != None and field.data != '' and field.data != [] and field.label not in set_fields:
                    set_fields.add(field.label)
                    if field.type == 'CheckboxField':
                        values.append(f"{field.label.text} : {', '.join(field.data)}")
                    else:
                        values.append(f"{field.label.text} : {field.data}")

    def all_page_setup(canvas, doc):
        canvas.saveState()
        canvas.setFont("Sarabun", 12)
        page_number = canvas.getPageNumber()
        canvas.drawString(530, 30, f"Page {page_number}")
        canvas.restoreState()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            rightMargin=20,
                            leftMargin=20,
                            topMargin=10,
                            bottomMargin=10
                            )

    data = []

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=style_sheet['ThaiStyle'],
        fontSize=15,
        alignment=TA_CENTER,
    )

    header = Table([[Paragraph('<b>ใบขอรับบริการ / Request</b>', style=header_style)]], colWidths=[530],
                   rowHeights=[25])

    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    lab_address = '''<para><font size=12>
                    {address}
                    </font></para>'''.format(address=lab.address if lab else sub_lab.address)

    lab_table = Table([[logo, Paragraph(lab_address, style=style_sheet['ThaiStyle'])]], colWidths=[45, 330])

    lab_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    staff_only = '''<para><font size=12>
                สำหรับเจ้าหน้าที่ / Staff only<br/>
                เลขที่ใบคำขอ &nbsp;&nbsp;_____________<br/>
                วันที่รับตัวอย่าง _____________<br/>
                วันที่รายงานผล _____________<br/>
                </font></para>'''

    staff_table = Table([[Paragraph(staff_only, style=style_sheet['ThaiStyle'])]], colWidths=[150])

    staff_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))

    content_header = Table([[Paragraph('<b>รายละเอียด / Detail</b>', style=header_style)]], colWidths=[530],
                           rowHeights=[25])

    content_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    detail_style = ParagraphStyle(
        'ThaiStyle',
        parent=style_sheet['ThaiStyle'],
        fontSize=12,
        leading=18
    )
    customer = '''<para>ข้อมูลผู้ส่งตรวจ<br/>
                        ผู้ส่ง : {customer}<br/>
                        เบอร์โทรศัพท์ : {phone_number}<br/>
                        ที่อยู่ : {address}<br/>
                        อีเมล : {email}
                    </para>
                    '''.format(customer=service_request.customer_account.customer_info.cus_name,
                               address=', '.join([address.address for address in service_request.customer_account.customer_info.addresses if address.address_type == 'customer']),
                               phone_number=service_request.customer_account.customer_info.phone_number,
                               email=service_request.customer_account.customer_info.email)

    customer_table = Table([[Paragraph(customer, style=detail_style)]], colWidths=[530])

    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    data.append(KeepTogether(Spacer(7, 7)))
    data.append(KeepTogether(Paragraph('<para align=center><font size=18>ใบขอรับบริการ / REQUEST<br/><br/></font></para>',
                                       style=style_sheet['ThaiStyle'])))
    data.append(KeepTogether(header))
    data.append(KeepTogether(Spacer(3, 3)))
    data.append(KeepTogether(Table([[lab_table, staff_table]], colWidths=[378, 163])))
    data.append(KeepTogether(Spacer(3, 3)))
    data.append(KeepTogether(content_header))
    data.append(KeepTogether(Spacer(7, 7)))
    data.append(KeepTogether(customer_table))

    details = 'ข้อมูลผลิตภัณฑ์' + "<br/>" + "<br/>".join(values)
    first_page_limit = 500
    remaining_text = ""
    current_length = 0

    lines = details.split("<br/>")
    first_page_lines = []
    for line in lines:
        if current_length + detail_style.leading <= first_page_limit:
            first_page_lines.append(line)
            current_length += detail_style.leading
        else:
            remaining_text += line + "<br/>"

    first_page_text = "<br/>".join(first_page_lines)
    first_page_paragraph = Paragraph(first_page_text, style=detail_style)

    if remaining_text:
        remaining_paragraph = Paragraph(remaining_text, style=detail_style)

    first_page_table = [[first_page_paragraph]]
    first_page_table = Table(first_page_table, colWidths=[530])
    first_page_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    data.append(KeepTogether(first_page_table))

    if remaining_text:
        data.append(PageBreak())
        remaining_table = [[remaining_paragraph]]
        remaining_table = Table(remaining_table, colWidths=[530])
        remaining_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        data.append(KeepTogether(Spacer(20, 20)))
        data.append(KeepTogether(content_header))
        data.append(KeepTogether(Spacer(7, 7)))
        data.append(KeepTogether(remaining_table))
    lab_test = '''<para><font size=12>
                    สำหรับเจ้าหน้าที่<br/>
                    Lab No. : __________________________________<br/>
                    สภาพตัวอย่าง : O ปกติ<br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; O ไม่ปกติ<br/>
                    </font></para>'''

    lab_test_table = Table([[Paragraph(lab_test, style=detail_style)]], colWidths=[530])

    lab_test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    if service_request.lab == 'bacteria' or service_request.lab == 'virology':
        if remaining_text:
            data.append(KeepTogether(lab_test_table))
        else:
            data.append(KeepTogether(lab_test_table))

    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup)
    buffer.seek(0)
    return buffer


@service_admin.route('/request/pdf/<int:request_id>', methods=['GET'])
def export_request_pdf(request_id):
    service_request = ServiceRequest.query.get(request_id)
    buffer = generate_request_pdf(service_request)
    return send_file(buffer, download_name='Request_form.pdf', as_attachment=True)


@service_admin.route('/result/index')
def result_index():
    return render_template('service_admin/result_index.html')


@service_admin.route('/api/result/index')
def get_results():
    query = ServiceResult.query.filter_by(admin_id=current_user.id)
    records_total = query.count()
    search = request.args.get('search[value]')
    if search:
        query = query.filter(ServiceRequest.created_at.contains(search))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        if item.file_result:
            file_upload = drive.CreateFile({'id': item.url})
            file_upload.FetchMetadata()
            item_data['file'] = file_upload.get('embedLink')
        else:
            item_data['file'] = None
        data.append(item_data)
    return jsonify({'data': data,
                    'recordFiltered': total_filtered,
                    'recordTotal': records_total,
                    'draw': request.args.get('draw', type=int)
                    })


@service_admin.route('/result/add', methods=['GET', 'POST'])
@service_admin.route('/result/edit/<int:result_id>', methods=['GET', 'POST'])
def create_result(result_id=None):
    if result_id:
        result = ServiceResult.query.get(result_id)
        form = ServiceResultForm(obj=result)
    else:
        form = ServiceResultForm()
    if form.validate_on_submit():
        if result_id is None:
            result = ServiceResult()
        form.populate_obj(result)
        file = form.file_upload.data
        result.admin_id = current_user.id
        if result_id:
            result.modified_at = arrow.now('Asia/Bangkok').datetime
        else:
            result.released_at = arrow.now('Asia/Bangkok').datetime
        result.status = 'ออกใบรายงายผลการทดสอบ'
        drive = initialize_gdrive()
        if file:
            file_name = secure_filename(file.filename)
            file.save(file_name)
            file_drive = drive.CreateFile({'title': file_name,
                                           'parents': [{'id': FOLDER_ID, "kind": "drive#fileLink"}]})
            file_drive.SetContentFile(file_name)
            file_drive.Upload()
            permission = file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
            result.url = file_drive['id']
            result.file_result = file_name
        db.session.add(result)
        db.session.commit()
        scheme = 'http' if current_app.debug else 'https'
        service_request = ServiceRequest.query.get(result.request_id)
        customer_email = service_request.customer_account.customer_info.email
        result_link = url_for('academic_services.result_index', _external=True, _scheme=scheme)
        if result_id:
            title = 'แจ้งแก้ไขและออกใบรายงานผลการทดสอบใหม่'
            message = f'''ทางหน่วยงานได้แก้ไขและทำการออกใบรายงานผลการทดสอบใหม่เป็นที่เรียบร้อยแล้ว ท่านสามมารถตรวจสอบได้ที่ลิ้งค์ข้างล่างนี้\n'''
            message += f'''{result_link}'''
            send_mail([customer_email], title, message)
            flash('แก้ไขรายงานผลการทดสอบเรียบร้อย', 'success')
        else:
            title = 'แจ้งออกใบรายงานผลการทดสอบ'
            message = f'''ทางหน่วยงานได้ทำการออกใบรายงานผลการทดสอบเป็นที่เรียบร้อยแล้ว ท่านสามมารถตรวจสอบได้ที่ลิ้งค์ข้างล่างนี้\n'''
            message += f'''{result_link}'''
            send_mail([customer_email], title, message)
            flash('สร้างรายงานผลการทดสอบเรียบร้อย', 'success')
        return redirect(url_for('service_admin.result_index'))
    return render_template('service_admin/create_result.html', form=form, result_id=result_id)


@service_admin.route('/payment/index')
def payment_index():
    return render_template('service_admin/payment_index.html')


@service_admin.route('/api/payment/index')
def get_payments():
    admin = ServiceAdmin.query.filter_by(admin_id=current_user.id).all()
    labs = []
    sub_labs = []
    for a in admin:
        if a.lab:
            labs.append(a.lab.code)
        else:
            sub_labs.append(a.sub_lab.code)
    query = ServiceRequest.query.filter(
        and_(
            or_(ServiceRequest.admin.has(id=current_user.id),ServiceRequest.lab.in_(labs))),
        or_(
            ServiceRequest.status == 'ยังไม่ชำระเงิน',
            ServiceRequest.status == 'รอเจ้าหน้าที่ตรวจสอบการชำระเงิน',
            ServiceRequest.status == 'ชำระเงินไม่สำเร็จ',
            ServiceRequest.status == 'ชำระเงินสำเร็จ'
        )
    ) \
        if labs else ServiceRequest.query.filter(
        and_(
            or_(ServiceRequest.admin.has(id=current_user.id), ServiceRequest.lab.in_(sub_labs))),
        or_(
            ServiceRequest.status == 'ยังไม่ชำระเงิน',
            ServiceRequest.status == 'รอเจ้าหน้าที่ตรวจสอบการชำระเงิน',
            ServiceRequest.status == 'ชำระเงินไม่สำเร็จ',
            ServiceRequest.status == 'ชำระเงินสำเร็จ'
        )
    )
    records_total = query.count()
    search = request.args.get('search[value]')
    if search:
        query = query.filter(ServiceRequest.created_at.contains(search))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        if item.payment and item.payment.url:
            file_upload = drive.CreateFile({'id': item.payment.url})
            file_upload.FetchMetadata()
            item_data['file'] = f"https://drive.google.com/uc?export=download&id={item.payment.url}"
        else:
            item_data['file'] = None
        data.append(item_data)
    return jsonify({'data': data,
                    'recordFiltered': total_filtered,
                    'recordTotal': records_total,
                    'draw': request.args.get('draw', type=int)
                    })


@service_admin.route('/payment/confirm/<int:request_id>', methods=['GET'])
def confirm_payment(request_id):
    service_request = ServiceRequest.query.get(request_id)
    service_request.is_paid = True
    service_request.status = 'ชำระเงินสำเร็จ'
    service_request.payment.status = 'ชำระเงินสำเร็จ'
    db.session.add(service_request)
    db.session.commit()
    flash('เปลี่ยนสถานะสำเร็จ', 'success')
    return redirect(url_for('service_admin.payment_index'))


@service_admin.route('/payment/cancel/<int:request_id>', methods=['GET'])
def cancel_payment(request_id):
    service_request = ServiceRequest.query.get(request_id)
    service_request.is_paid = False
    service_request.status = 'ชำระเงินไม่สำเร็จ'
    service_request.payment.status = 'ชำระเงินไม่สำเร็จ'
    db.session.add(service_request)
    db.session.commit()
    flash('เปลี่ยนสถานะสำเร็จ', 'success')
    return redirect(url_for('service_admin.payment_index'))