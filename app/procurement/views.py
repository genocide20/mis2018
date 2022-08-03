# -*- coding:utf-8 -*-
import cStringIO
import os, requests
from base64 import b64decode

from flask import render_template, request, flash, redirect, url_for, send_file
from flask_login import current_user, login_required
from reportlab.lib.units import mm

from werkzeug.utils import secure_filename
from . import procurementbp as procurement
from .forms import *
from datetime import datetime, timedelta
from pytz import timezone
from reportlab.platypus import (SimpleDocTemplate, Table, Image,
                                Spacer, Paragraph, TableStyle, PageBreak, Frame)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
import qrcode
from reportlab.platypus import Image
from reportlab.graphics.barcode import qr
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib import colors


style_sheet = getSampleStyleSheet()
style_sheet.add(ParagraphStyle(name='ThaiStyle', fontName='Sarabun'))
style_sheet.add(ParagraphStyle(name='ThaiStyleNumber', fontName='Sarabun', alignment=TA_RIGHT))
style_sheet.add(ParagraphStyle(name='ThaiStyleCenter', fontName='Sarabun', alignment=TA_CENTER))

# Upload images for Google Drive


FOLDER_ID = "1JYkU2kRvbvGnmpQ1Tb-TcQS-vWQKbXvy"

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()

bangkok = timezone('Asia/Bangkok')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@procurement.route('/new/add', methods=['GET', 'POST'])
@login_required
def add_procurement():
    form = CreateProcurementForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            procurement = ProcurementDetail()
            form.populate_obj(procurement)
            procurement.creation_date = bangkok.localize(datetime.now())
            procurement.staff = current_user
            procurement.end_guarantee_date = form.start_guarantee_date.data + timedelta(days=int(form.days.data))
            # TODO: calculate end date from time needed to finish guarantee date
            file = form.image.data
            print(form.image.data)
            if file:
                img_name = secure_filename(file.filename)
                file.save(img_name)
                # convert image to base64(text) in database
                import base64
                with open(img_name, "rb") as img_file:
                    procurement.image = base64.b64encode(img_file.read())

            else:
                # convert base64(text) to image in database
                decoded_img = b64decode(procurement.image)
                img_string = cStringIO.StringIO(decoded_img)
                img_string.seek(0)
            record = ProcurementRecord(location=form.location.data, staff=current_user,
                                       status=form.status.data, updated_at= bangkok.localize(datetime.now()))
            procurement.records.append(record)
            db.session.add(procurement)
            db.session.commit()
            flash(u'บันทึกข้อมูลสำเร็จ.', 'success')
            return redirect(url_for('procurement.view_procurement'))
        # Check Error
        else:
            for er in form.errors:
                flash(er, 'danger')
    return render_template('procurement/new_procurement.html', form=form)


@procurement.route('/landing')
def landing():
    return render_template('procurement/landing.html')


@procurement.route('/information/all')
@login_required
def view_procurement():
    procurement_list = []
    procurement_query = ProcurementDetail.query.all()
    for procurement in procurement_query:
        record = {}
        record["id"] = procurement.id
        record["name"] = procurement.name
        record["procurement_no"] = procurement.procurement_no
        record["erp_code"] = procurement.erp_code
        record["budget_year"] = procurement.budget_year
        record["received_date"] = procurement.received_date
        record["bought_by"] = procurement.bought_by
        record["available"] = procurement.available
        procurement_list.append(record)
    return render_template('procurement/view_all_data.html', procurement_list=procurement_list)


@procurement.route('/information/find', methods=['POST', 'GET'])
@login_required
def find_data():
    return render_template('procurement/find_data.html')


@procurement.route('/edit/<int:procurement_id>', methods=['GET', 'POST'])
@login_required
def edit_procurement(procurement_id):
    procurement = ProcurementDetail.query.get(procurement_id)
    form = CreateProcurementForm(obj=procurement)
    if request.method == 'POST':
        form.populate_obj(procurement)
        db.session.add(procurement)
        db.session.commit()
        flash(u'แก้ไขข้อมูลเรียบร้อย', 'success')
        return redirect(url_for('procurement.view_procurement'))
    return render_template('procurement/edit_procurement.html', form=form, procurement=procurement)


@procurement.route('/qrcode/view/<int:procurement_id>')
@login_required
def view_qrcode(procurement_id):
    item = ProcurementDetail.query.get(procurement_id)
    return render_template('procurement/view_qrcode.html',
                           model=ProcurementRecord,
                           item=item,
                           procurement_no=item.procurement_no)


@procurement.route('/items/<int:item_id>/records/add', methods=['GET', 'POST'])
@login_required
def add_record(item_id):
    form = ProcurementRecordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_record = ProcurementRecord()
            form.populate_obj(new_record)
            new_record.item_id = item_id
            new_record.staff = current_user
            new_record.updated_at = datetime.now(tz=bangkok)
            db.session.add(new_record)
            db.session.commit()
            flash('New Record Has Been Added.', 'success')
            return redirect(url_for('procurement.view_procurement'))
    return render_template('procurement/record_form.html', form=form)


@procurement.route('/category/add', methods=['GET', 'POST'])
def add_category_ref():
    category = db.session.query(ProcurementCategory)
    form = ProcurementCategoryForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_category = ProcurementCategory()
            form.populate_obj(new_category)
            db.session.add(new_category)
            db.session.commit()
            flash('New category has been added.', 'success')
            return redirect(url_for('procurement.add_procurement'))
    return render_template('procurement/category_ref.html', form=form, category=category)


@procurement.route('/status/add', methods=['GET', 'POST'])
def add_status_ref():
    status = db.session.query(ProcurementStatus)
    form = ProcurementStatusForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_status = ProcurementStatus()
            form.populate_obj(new_status)
            db.session.add(new_status)
            db.session.commit()
            flash('New status has been added.', 'success')
            return redirect(url_for('procurement.add_procurement'))
    return render_template('procurement/status_ref.html', form=form, status=status)


@procurement.route('/service/maintenance/require')
def require_maintenance():
    return render_template('procurement/require_maintenance.html')


@procurement.route('/service/list', methods=['POST', 'GET'])
def list_maintenance():
    if request.method == 'GET':
        maintenance_query = ProcurementDetail.query.all()
    else:
        procurement_number = request.form.get('procurement_number', None)
        users = request.form.get('users', 0)
        if procurement_number:
            maintenance_query = ProcurementDetail.query.filter(ProcurementDetail.procurement_no.like('%{}%'.format(procurement_number)))
        else:
            maintenance_query = []
        if request.headers.get('HX-Request') == 'true':
            return render_template('procurement/partials/maintenance_list.html', maintenance_query=maintenance_query)

    return render_template('procurement/maintenance_list.html', maintenance_query=maintenance_query)


@procurement.route('/service/contact', methods=['GET', 'POST'])
def contact_service():
    # if request.method == 'POST':
    #     service_id = request.form.get('service_id', None)
    #     record_id = request.form.get('record_id', None)
    #     service = request.form.get('service', ''),
    #     desc = request.form.get('desc', ''),
    #     notice_date = request.form.get('notice_date', '')
    #     require = ProcurementRequire.query.get(require_id)
    #     tz = pytz.timezone('Asia/Bangkok')
    #     if notice_date:
    #         noticedate = parser.isoparse(notice_date)
    #         noticedate = noticedate.astimezone(tz)
    #     else:
    #         noticedate = None
    #
    #     if require_id and noticedate:
    #         approval_needed = True if service.available == 2 else False
    #
            # new_maintenance = ProcurementRequire(service_id=service.id,
            #                                      record_id=record.id,
            #                                      staff_id=current_user.id,
            #                                      desc=desc,
            #                                      notice_date=notice_date)

    #         db.session.add(new_maintenance)
    #         db.session.commit()
    #         flash(u'บันทึกการจองห้องเรียบร้อยแล้ว', 'success')
    #         return redirect(url_for(''))
    return render_template('procurement/maintenance_contact.html')


@procurement.route('/maintenance/all')
@login_required
def view_maintenance():
    maintenance_list = []
    maintenance_query = ProcurementRequire.query.all()
    for maintenance in maintenance_query:
        record = {}
        record["id"] = maintenance.id
        record["service"] = maintenance.service
        record["notice_date"] = maintenance.notice_date
        record["explan"] = maintenance.explan
        maintenance_list.append(record)
    return render_template('procurement/view_all_maintenance.html', maintenance_list=maintenance_list)


@procurement.route('/maintenance/user/require')
@login_required
def view_require_service():
    require_list = []
    maintenance_query = ProcurementRequire.query.all()
    for maintenance in maintenance_query:
        record = {}
        record["id"] = maintenance.id
        record["service"] = maintenance.service
        record["notice_date"] = maintenance.notice_date
        record["explan"] = maintenance.explan
        require_list.append(record)
    return render_template('procurement/view_by_ITxRepair.html', require_list=require_list)


@procurement.route('/service/<int:service_id>/update', methods=['GET', 'POST'])
@login_required
def update_record(service_id):
    form = ProcurementMaintenanceForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            update_record = ProcurementMaintenance()
            form.populate_obj(update_record)
            update_record.service_id = service_id
            update_record.staff = current_user
            db.session.add(update_record)
            db.session.commit()
            flash('Update record has been added.', 'success')
            return redirect(url_for('procurement.view_require_service'))
    return render_template('procurement/update_by_ITxRepair.html', form=form)


@procurement.route('/qrcode/scanner')
def qrcode_scanner():
    return render_template('procurement/qr_scanner.html')


@procurement.route('/qrcode/render/<string:procurement_no>')
def qrcode_render(procurement_no):
    item = ProcurementDetail.query.filter_by(procurement_no=procurement_no)
    return render_template('procurement/qrcode_render.html',
                           item=item)


@procurement.route('/qrcode/list')
def list_qrcode():
    qrcode_list = []
    procurement_query = ProcurementDetail.query.all()
    for procurement in procurement_query:
        record = {}
        record["id"] = procurement.id
        record["name"] = procurement.name
        record["procurement_no"] = procurement.procurement_no
        record["budget_year"] = procurement.budget_year
        record["responsible_person"] = procurement.responsible_person
        qrcode_list.append(record)
    return render_template('procurement/list_qrcode.html', qrcode_list=qrcode_list)


@procurement.route('/qrcode/pdf/list/<int:procurement_id>')
def export_qrcode_pdf(procurement_id):
    procurement = ProcurementDetail.query.get(procurement_id)

    def all_page_setup(canvas, doc):
        canvas.saveState()
        # logo_image = ImageReader('app/static/img/mumt-logo.png')
        # canvas.drawImage(logo_image, 10, 700, width=250, height=100)
        canvas.restoreState()

    doc = SimpleDocTemplate("app/qrcode.pdf",
                            rightMargin=10,
                            leftMargin=10,
                            topMargin=10,
                            bottomMargin=10,
                            pagesize=(480, 480)
                            )
    data = []
    if not procurement.qrcode:
        qr = qrcode.QRCode(version=1, box_size=20)
        qr.add_data(procurement.procurement_no)
        qr.make(fit=True)
        qr_img = qr.make_image()
        qr_img.save('procurement_qrcode.png')
        import base64
        with open("procurement_qrcode.png", "rb") as img_file:
            procurement.qrcode = base64.b64encode(img_file.read())
            db.session.add(procurement)
            db.session.commit()

    decoded_img = b64decode(procurement.qrcode)
    img_string = cStringIO.StringIO(decoded_img)
    img_string.seek(0)
    im = Image(img_string, 100 * mm, 100 * mm, kind='bound')
    data.append(im)

    data.append(Paragraph('<para align=center><font size=18>{}<br/><br/></font></para>'
                          .format(procurement.procurement_no.encode('utf-8')),
                          style=style_sheet['ThaiStyle']))
    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup)
    return send_file('qrcode.pdf')


@procurement.route('/qrcode/list/pdf/all')
def export_all_qrcode_pdf():
    procurement_query = ProcurementDetail.query.all()

    def all_page_setup(canvas, doc):
        canvas.saveState()
        # logo_image = ImageReader('app/static/img/mumt-logo.png')
        # canvas.drawImage(logo_image, 10, 700, width=250, height=100)
        canvas.restoreState()

    doc = SimpleDocTemplate("app/all_qrcode.pdf",
                            rightMargin=20,
                            leftMargin=20,
                            topMargin=20,
                            bottomMargin=10,
                            pagesize=letter
                            )
    data = []
    for procurement in procurement_query:
        if not procurement.qrcode:
            qr_img = qrcode.make(procurement.procurement_no, box_size=4)
            qr_img.save('procurement{}.png'.format(id))
            # convert image to base64(text) in database
            import base64
            with open("procurement_qrcode.png", "rb") as img_file:
                procurement.qrcode = base64.b64encode(img_file.read())
                db.session.add(procurement)
                db.session.commit()
        else:
            # convert base64(text) to image in database
            decoded_img = b64decode(procurement.qrcode)
            img_string = cStringIO.StringIO(decoded_img)
            img_string.seek(0)
            im = Image(img_string, 50 * mm, 50 * mm, kind='bound')
            data.append(im)

        data.append(Paragraph('<para align=center><font size=18>รหัสครุภัณฑ์ / Procurement No: {}<br/><br/></font></para>'
                              .format(procurement.procurement_no.encode('utf-8')),
                              style=style_sheet['ThaiStyle']))
    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup)
    return send_file('all_qrcode.pdf')
