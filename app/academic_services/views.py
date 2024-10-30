import arrow
import pandas
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, TableStyle, Table, Spacer, PageBreak, KeepTogether

from app.main import app, get_credential, json_keyfile
from app.academic_services import academic_services
from app.academic_services.forms import (create_customer_form, LoginForm, ForgetPasswordForm, ResetPasswordForm,
                                         ServiceCustomerAccountForm, create_request_form)
from app.academic_services.models import *
from flask import render_template, flash, redirect, url_for, request, current_app, abort, session, make_response, \
    jsonify, send_file
from flask_login import login_user, current_user, logout_user, login_required
from flask_principal import Identity, identity_changed, AnonymousIdentity
from flask_admin.helpers import is_safe_url
from itsdangerous.url_safe import URLSafeTimedSerializer as TimedJSONWebSignatureSerializer
from app.main import mail
from flask_mail import Message

sarabun_font = TTFont('Sarabun', 'app/static/fonts/THSarabunNew.ttf')
pdfmetrics.registerFont(sarabun_font)
style_sheet = getSampleStyleSheet()
style_sheet.add(ParagraphStyle(name='ThaiStyle', fontName='Sarabun'))
style_sheet.add(ParagraphStyle(name='ThaiStyleNumber', fontName='Sarabun', alignment=TA_RIGHT))
style_sheet.add(ParagraphStyle(name='ThaiStyleCenter', fontName='Sarabun', alignment=TA_CENTER))


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


@academic_services.route('/')
@login_required
def index():
    return render_template('academic_services/index.html')


@academic_services.route('/lab/index')
@login_required
def lab_index():
    lab = request.args.get('lab')
    return render_template('academic_services/lab_index.html', lab=lab)


@academic_services.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_url = request.args.get('next', url_for('academic_services.customer_account'))
        if is_safe_url(next_url):
            return redirect(next_url)
        else:
            return abort(400)
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(ServiceCustomerAccount).filter_by(email=form.email.data).first()
        if user:
            pwd = form.password.data
            if user.verify_password(pwd):
                login_user(user)
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                next_url = request.args.get('next', url_for('index'))
                if not is_safe_url(next_url):
                    return abort(400)
                else:
                    flash('ลงทะเบียนเข้าใช้งานสำเร็จ', 'success')
                    return redirect(url_for('academic_services.customer_account', menu='view'))
            else:
                flash('รหัสผ่านไม่ถูกต้อง กรุณาลองอีกครั้ง', 'danger')
                return redirect(url_for('academic_services.login'))
        else:
            flash('ไม่พบบัญชีผู้ใช้งาน', 'danger')
            return redirect(url_for('academic_services.login'))
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('academic_services/login.html', form=form)


@academic_services.route('/logout')
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    flash('ออกจากระบบเรียบร้อย', 'success')
    return redirect(url_for('academic_services.login'))


@academic_services.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect('academic_services.customer_account')
    form = ForgetPasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = ServiceCustomerAccount.query.filter_by(email=form.email.data).first()
            if not user:
                flash('ไม่พบบัญชีผู้ใช้งาน', 'warning')
                return render_template('academic_services/forget_password.html', form=form, errors=form.errors)
            serializer = TimedJSONWebSignatureSerializer(app.config.get('SECRET_KEY'))
            token = serializer.dumps({'email': form.email.data})
            url = url_for('academic_services.reset_password', token=token, _external=True)
            message = 'Click the link below to reset the password.'\
                      ' กรุณาคลิกที่ลิงค์เพื่อทำการตั้งรหัสผ่านใหม่\n\n{}'.format(url)
            try:
                send_mail([form.email.data],
                          title='MUMT-MIS: Password Reset. ตั้งรหัสผ่านใหม่สำหรับระบบ MUMT-MIS',
                          message=message)
            except:
                flash('ระบบไม่สามารถส่งอีเมลได้กรุณาตรวจสอบอีกครั้ง'.format(form.email.data),'danger')
            else:
                flash('โปรดตรวจสอบอีเมลของท่านเพื่อทำการแก้ไขรหัสผ่านภายใน 20 นาที', 'success')
            return redirect(url_for('academic_services.login'))
        else:
            for er in form.errors:
                flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('academic_services/forget_password.html', form=form)


@academic_services.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    serializer = TimedJSONWebSignatureSerializer(app.config.get('SECRET_KEY'))
    try:
        token_data = serializer.loads(token, max_age=72000)
    except:
        return 'รหัสสำหรับทำการตั้งค่า password หมดอายุหรือไม่ถูกต้อง'
    user = ServiceCustomerAccount.query.filter_by(email=token_data.get('email')).first()
    if not user:
        flash('ไม่พบชื่อบัญชีในฐานข้อมูล')
        return redirect(url_for('academic_services.login'))

    form = ResetPasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user.password = form.new_password.data
            db.session.add(user)
            db.session.commit()
            flash('ตั้งรหัสผ่านใหม่เรียบร้อย', 'success')
            return redirect(url_for('academic_services.login'))
        else:
            for er in form.errors:
                flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('academic_services/reset_password.html', form=form)


@academic_services.route('/customer/index')
def customer_index():
    return render_template('academic_services/customer_index.html')


@academic_services.route('/customer/view', methods=['GET', 'POST'])
def customer_account():
    menu = request.args.get('menu')
    return render_template('academic_services/customer_account.html', menu=menu)


@academic_services.route('/customer/add', methods=['GET', 'POST'])
def create_customer_account(customer_id=None):
    menu = request.args.get('menu')
    form = ServiceCustomerAccountForm()
    if form.validate_on_submit():
        customer = ServiceCustomerAccount()
        form.populate_obj(customer)
        if current_user.is_authenticated:
            customer.customer_info.creator_id = current_user.id
            customer.verify_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(customer)
        db.session.commit()
        serializer = TimedJSONWebSignatureSerializer(app.config.get('SECRET_KEY'))
        token = serializer.dumps({'email': form.email.data})
        scheme = 'http' if current_app.debug else 'https'
        url = url_for('academic_services.verify_email', token=token, _external=True, _scheme=scheme)
        message = 'Click the link below to confirm.' \
                    ' กรุณาคลิกที่ลิงค์เพื่อทำการยืนยันการสมัครบัญชีระบบ MUMT-MIS\n\n{}'.format(url)
        send_mail([form.email.data], title='ยืนยันการสมัครบัญชีระบบ MUMT-MIS', message=message)
        flash('โปรดตรวจสอบอีเมลของท่านผ่านภายใน 20 นาที', 'success')
        return redirect(url_for('academic_services.login'))
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('academic_services/create_customer.html', form=form, customer_id=customer_id,
                           menu=menu)


@academic_services.route('/email-verification', methods=['GET', 'POST'])
def verify_email():
    token = request.args.get('token')
    serializer = TimedJSONWebSignatureSerializer(app.config.get('SECRET_KEY'))
    try:
        token_data = serializer.loads(token, max_age=72000)
    except:
        return 'รหัสสำหรับทำการสมัครบัญชีหมดอายุหรือไม่ถูกต้อง'
    user = ServiceCustomerAccount.query.filter_by(email=token_data.get('email')).first()
    if not user:
        flash('ไม่พบชื่อบัญชีผู้ใช้งาน กรุณาลงทะเบียนใหม่อีกครั้ง', 'danger')
    elif user.verify_datetime:
        flash('ได้รับการยืนยันอีเมลแล้ว', 'info')
    else:
        user.verify_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(user)
        db.session.commit()
        flash('ยืนยันอีเมลเรียบร้อยแล้ว', 'success')
    return redirect(url_for('academic_services.login'))


@academic_services.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer_account(customer_id):
    menu = request.args.get('menu')
    customer = ServiceCustomerInfo.query.get(customer_id)
    ServiceCustomerInfoForm = create_customer_form(type=None)
    form = ServiceCustomerInfoForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        if form.same_address.data:
            customer.quotation_address = form.document_address.data
        db.session.add(customer)
        db.session.commit()
        flash('แก้ไขข้อมูลบัญชีสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('academic_services/modal/edit_customer_modal.html', form=form, menu=menu,
                           customer_id=customer_id, customer=customer)


@academic_services.route('/edit_password', methods=['GET', 'POST'])
def edit_password():
    menu = request.args.get('menu')
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password and confirm_password:
            if new_password == confirm_password:
                current_user.password = new_password
                db.session.add(current_user)
                db.session.commit()
                flash('รหัสผ่านแก้ไขแล้ว', 'success')
            else:
                flash('รหัสผ่านไม่ตรงกัน', 'danger')
        else:
            flash('กรุณากรอกรหัสใหม่', 'danger')
    return render_template('academic_services/edit_password.html', menu=menu)


@academic_services.route('/customer/organization/add/<int:customer_id>', methods=['GET', 'POST'])
def add_organization(customer_id):
    customer = ServiceCustomerInfo.query.get(customer_id)
    ServiceCustomerInfoForm = create_customer_form(type='select')
    form = ServiceCustomerInfoForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        db.session.add(customer)
        db.session.commit()
        flash('เพิ่มบริษัท/องค์กรในข้อมูลบัญชีของท่านสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('academic_services/modal/add_organization_modal.html', form=form,
                           customer_id=customer_id)


@academic_services.route('/customer/organization/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_organization(customer_id):
    customer = ServiceCustomerInfo.query.get(customer_id)
    ServiceCustomerInfoForm = create_customer_form(type='form')
    form = ServiceCustomerInfoForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        if form.same_address.data:
            customer.quotation_address = form.document_address.data
        db.session.add(customer)
        db.session.commit()
        flash('แก้ไขข้อมูลบริษัท/องค์กรสำเร็จ', 'success')
        resp= make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    return render_template('academic_services/modal/edit_organization_modal.html', form=form,
                           customer_id=customer_id)


@academic_services.route('/admin/customer/view')
@login_required
def view_customer():
    customers = ServiceCustomerInfo.query.filter_by(creator=current_user)
    return render_template('academic_services/view_customer.html', customers=customers)


@academic_services.route('/admin/customer/add', methods=['GET', 'POST'])
@academic_services.route('/admin/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def create_customer_by_admin(customer_id=None):
    ServiceCustomerInfoForm = create_customer_form(type='select')
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
        if form.same_address.data:
            customer.quotation_address = form.document_address.data
        db.session.add(customer)
        db.session.commit()
        if customer_id:
            flash('แก้ไขข้อมูลลูกค้าสำเร็จ', 'success')
        else:
            flash('เพิ่มสร้างข้อมูลลูกค้าสำเร็จ', 'success')
        return redirect(url_for('academic_services.view_customer'))
    else:
        for er in form.errors:
            flash("{} {}".format(er, form.errors[er]), 'danger')
    return render_template('academic_services/create_customer_by_admin.html', customer_id=customer_id,
                           form=form)


@academic_services.route('/admin/customer/delete/<int:customer_id>', methods=['GET', 'DELETE'])
def delete_customer_by_admin(customer_id):
    if customer_id:
        customer = ServiceCustomerInfo.query.get(customer_id)
        db.session.delete(customer)
        db.session.commit()
        flash('ลบรายชื่อลูกค้าสำเร็จ', 'success')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp


@academic_services.route('/admin/customer/address/view/<int:customer_id>')
def view_customer_address(customer_id):
    customers = ServiceCustomerInfo.query.get(customer_id)
    return render_template('academic_services/modal/view_customer_address_modal.html', customers=customers)


@academic_services.route('/academic-service-form', methods=['GET'])
def get_request_form():
    menu = request.args.get('menu')
    sheetid = '1EHp31acE3N1NP5gjKgY-9uBajL1FkQe7CCrAu-TKep4'
    print('Authorizing with Google..')
    gc = get_credential(json_keyfile)
    wks = gc.open_by_key(sheetid)
    worksheet_mapping = {
        'product': "product_request",
        'foodsafety': "foodsafety_request",
        'heavymetal': "heavymetal_request",
        'mass_spectrometry': "mass_spectrometry_request",
        'quantitative': "quantitative_request",
        'toxicolab': "toxicolab_request",
        'virology': "virology_labora_request",
        'endotoxin': "endotoxin_request",
        '2d_gel': "2d_gel_electrophoresis_request",
    }
    sheet = wks.worksheet(worksheet_mapping.get(menu))
    df = pandas.DataFrame(sheet.get_all_records())
    form = create_request_form(df)()
    template = ''
    for f in form:
        template += str(f)
    return template


@academic_services.route('/academic-service-request', methods=['GET'])
def create_service_request():
    menu = request.args.get('menu')
    return render_template('academic_services/request_form.html', menu=menu)


@academic_services.route('/submit-request', methods=['POST'])
def submit_request():
    menu = request.args.get('menu')
    sheetid = '1EHp31acE3N1NP5gjKgY-9uBajL1FkQe7CCrAu-TKep4'
    gc = get_credential(json_keyfile)
    wks = gc.open_by_key(sheetid)
    worksheet_mapping = {
        'product': "product_request",
        'foodsafety': "foodsafety_request",
        'heavymetal': "heavymetal_request",
        'mass_spectrometry': "mass_spectrometry_request",
        'quantitative': "quantitative_request",
        'toxicolab': "toxicolab_request",
        'virology': "virology_labora_request",
        'endotoxin': "endotoxin_request",
        '2d_gel': "2d_gel_electrophoresis_request",
    }
    sheet = wks.worksheet(worksheet_mapping.get(menu))
    df = pandas.DataFrame(sheet.get_all_records())
    form = request.form
    field_group_index = {}
    data = []
    for idx, row in df.iterrows():
        field_group = row['fieldGroup']
        if field_group not in field_group_index:
            field_group_index[field_group] = len(data)
            data.append([field_group, []])
        field_name = row['fieldName']
        if row['formFieldName']:
            for i in range(len(row['formFieldName'])):
                form_key = f"{field_group}-{row['formFieldName']}-{i}-{field_name}"
                value = form.getlist(form_key) if row['fieldType'] == 'multichoice' else form.get(form_key, '')
                data[field_group_index[field_group]][1].append([field_name, value])
        else:
            form_key = f"{field_group}-{field_name}"
            value = form.getlist(form_key) if row['fieldType'] == 'multichoice' else form.get(form_key, '')
            data[field_group_index[field_group]][1].append([field_name, value])
    if hasattr(current_user, 'personal_info'):
        record = ServiceRequest(admin=current_user, created_at=arrow.now('Asia/Bangkok').datetime, lab=menu, data=data)
    elif hasattr(current_user, 'customer_info'):
        record = ServiceRequest(customer=current_user.customer_info, created_at=arrow.now('Asia/Bangkok').datetime,
                                lab=menu, data=data)
    db.session.add(record)
    db.session.commit()
    return redirect(url_for('academic_services.view_request', request_id=record.id))


@academic_services.route('/admin/request/index/<int:admin_id>')
@academic_services.route('/customer/request/index/<int:customer_id>')
@login_required
def request_index(admin_id=None, customer_id=None):
    return render_template('academic_services/request_index.html', admin_id=admin_id,
                           customer_id=customer_id)


@academic_services.route('/api/request/index')
def get_requests():
    admin_id = request.args.get('admin_id')
    customer_id = request.args.get('customer_id')
    query = ServiceRequest.query.filter_by(admin_id=admin_id) if admin_id else (ServiceRequest.query.
                                                                                filter_by(customer_id=customer_id))
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


@academic_services.route('/request/view/<int:request_id>')
@login_required
def view_request(request_id=None):
    request = ServiceRequest.query.get(request_id)
    return render_template('academic_services/view_request.html', request=request)


def generate_request_pdf(request, sign=False, cancel=False):
    logo = Image('app/static/img/logo-MU_black-white-2-1.png', 40, 40)
    formatted_data = []

    for section in request.data:
        section_name = section[0]
        fields = section[1]
        formatted_section = [f"{section_name}:"]

        for field in fields:
            field_name = field[0]
            field_value = field[1]
            if isinstance(field_value, list):
                formatted_value = ', '.join(field_value)
            else:
                formatted_value = field_value
            formatted_section.append(f"{field_name}: {formatted_value}")
        formatted_data.append("\n".join(formatted_section))

    def all_page_setup(canvas, doc):
        canvas.saveState()
        canvas.restoreState()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            rightMargin=1,
                            leftMargin=1,
                            topMargin=1,
                            bottomMargin=1,
                            pagesize=letter
                            )
    data = []

    lab_address = '''<para><font size=12>
                ห้องปฏิบัติการประเมินความปลอดภัยทางอาหารและชีวภาพ หน่วยตรวจวิเคราะห์ทางชีวภาพ<br/>
                คณะเทคนิคการแพทย์ มหาวิทยาลัยมหิดล<br/>
                เลขที่ 2 ถนนวังหลัง แขวงศิริราช เขตบำงกอกน้อย กรุงเทพฯ 10700<br/>
                โทร 02-419-7172, 065-523-3387 เลขที่ผู้เสียภาษี 0994000158378<br/>
                </font></para>
                '''

    lab = Table([[logo, Paragraph(lab_address, style=style_sheet['ThaiStyle'])]],
                         colWidths=[45, 400])

    lab.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    staff_only = '''<para><font size=12>
                สำหรับเจ้าหน้าที่ / Staff only<br/>
                เลขที่ใบคำขอ ______________<br/>
                วันที่รับตัวอย่ำง _____________<br/>
                วันที่รายงานผล _____________<br/>
                </font></para>'''

    staff = Table([[Paragraph(staff_only, style=style_sheet['ThaiStyle'])]], colWidths=[140, 350])
    staff.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    parent_table = Table([[lab, staff]], colWidths=[300, 300])
    parent_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (1, 0), (1, 0), 155),
    ]))
    header = Table([[Paragraph('ใบขอรับบริการ / Request form', style=style_sheet['ThaiStyle'])]],
                        colWidths=[580])

    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    header_content = [
        [Paragraph(text, style=style_sheet['ThaiStyle']) for text in formatted_data],
        [Paragraph("ภายใน 2", style=style_sheet['ThaiStyle'])]
    ]

    content = Table(header_content, colWidths=[300])
    content.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.blue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    data.append(parent_table)
    data.append(header)
    data.append(Spacer(1, 10))
    data.append(content)
    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup)
    buffer.seek(0)
    return buffer


@academic_services.route('/request/pdf/<int:request_id>', methods=['GET'])
def export_request_pdf(request_id):
    requests = ServiceRequest.query.get(request_id)
    buffer = generate_request_pdf(requests)
    return send_file(buffer, download_name='Request_form.pdf', as_attachment=True)