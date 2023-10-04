# -*- coding:utf-8 -*-
import os
from datetime import datetime
from io import BytesIO

import arrow

from app.e_sign_api import e_sign
import pytz
import requests
from bahttext import bahttext
from flask import render_template, request, flash, redirect, url_for, send_file, send_from_directory, make_response, \
    jsonify
from flask_login import current_user, login_required
from pandas import DataFrame
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, TableStyle, Table, Spacer, PageBreak, KeepTogether
from werkzeug.utils import secure_filename
from pydrive.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
from flask_mail import Message
from ..main import mail
from sqlalchemy import cast, Date, and_

from . import receipt_printing_bp as receipt_printing
from .forms import *
from .models import *
from ..comhealth.models import ComHealthReceiptID
from ..main import db
from ..roles import finance_permission, finance_head_permission

bangkok = pytz.timezone('Asia/Bangkok')

ALLOWED_EXTENSIONS = ['xlsx', 'xls']

FOLDER_ID = "1k_k0fAKnEEZaO3fhKwTLhv2_ONLam0-c"

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()


ALLOWED_EXTENSION = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@receipt_printing.route('/landing')
def landing():
    return render_template('receipt_printing/landing.html')


@receipt_printing.route('/receipt/create', methods=['POST', 'GET'])
def create_receipt():
    form = ReceiptDetailForm()
    form.payer.choices = [(None, 'Add or select payer')] + [(r.id, r.received_money_from)
                                for r in ElectronicReceiptReceivedMoneyFrom.query.all()]
    receipt_num = ComHealthReceiptID.get_number('MTS', db)
    payer = None
    if request.method == 'POST':
        if form.payer.data:
            try:
                payer_id = int(form.payer.data)
            except ValueError:
                payer = ElectronicReceiptReceivedMoneyFrom(received_money_from=form.payer.data)
                db.session.add(payer)
                db.session.commit()
            else:
                payer = ElectronicReceiptReceivedMoneyFrom.query.get(payer_id)

    if form.validate_on_submit():
        receipt_detail = ElectronicReceiptDetail()
        receipt_detail.issuer = current_user
        receipt_detail.created_datetime = datetime.now(tz=bangkok)
        form.populate_obj(receipt_detail)  #insert data from Form to Model
        if payer:
            receipt_detail.received_money_from = payer
        receipt_detail.number = receipt_num.number
        receipt_num.count += 1
        receipt_detail.received_money_from.address = form.address.data
        db.session.add(receipt_detail)
        db.session.add(receipt_num)
        db.session.commit()
        flash(u'บันทึกการสร้างใบเสร็จรับเงินสำเร็จ.', 'success')
        return redirect(url_for('receipt_printing.view_receipt_by_list_type'))
    # Check Error
    else:
        for er in form.errors:
            flash("{}:{}".format(er, form.errors[er]), 'danger')
    return render_template('receipt_printing/new_receipt.html', form=form)


@receipt_printing.route('/receipt/create/add-items', methods=['POST', 'GET'])
def list_add_items():
    form = ReceiptDetailForm()
    form.items.append_entry()
    item_form = form.items[-1]
    form_text = '<table class="table is-bordered is-fullwidth is-narrow">'
    form_text += u'''
    <div id={}>
        <div class="field">
            <label class="label">{}</label>
            <div class="control">
                {}
            </div>
        </div>
        <div class="field">
            <label class="label">{}</label>
            <div class="control">
                {}
            </div>
        </div>
        <div class="field">
            <label class="label">{}</label>
                {}
        </div>
        <div class="field">
            <label class="label">{}</label>
                {}
        </div>
        <div class="field">
            <label class="label">{}</label>
                {}
        </div>
    </div>
    '''.format(item_form.name, item_form.item.label, item_form.item(class_="textarea"), item_form.price.label,
               item_form.price(class_="input", type="text", placeholder=u"฿", onkeyup="update_amount()"),
               item_form.gl.label, item_form.gl(),
               item_form.cost_center.label, item_form.cost_center(),
               item_form.internal_order_code.label, item_form.internal_order_code()
               )
    resp = make_response(form_text)
    resp.headers['HX-Trigger-After-Swap'] = 'initInput'
    return resp


@receipt_printing.route('/receipt/create/items-delete', methods=['POST', 'GET'])
def delete_items():
    form = ReceiptDetailForm()
    if len(form.items.entries) > 1:
        form.items.pop_entry()
        alert = False
    else:
        alert = True
    form_text = ''
    for item_form in form.items.entries:
        form_text += u'''
    <div id={} hx-preserve>
        <div class="field">
            <label class="label">{}</label>
            <div class="control">
                {}
            </div>
        </div>
        <div class="field">
            <label class="label">{}</label>
            <div class="control">
                {}
            </div>
        </div>
        <div class="field" hx-preserve>
            <label class="label">{}</label>
                {}
        </div>
        <div class="field" hx-preserve>
            <label class="label">{}</label>
                {}
        </div>
        <div class="field" hx-preserve>
            <label class="label">{}</label>
                {}
        </div>
    </div>
    '''.format(item_form.name, item_form.item.label, item_form.item(class_="textarea"), item_form.price.label,
               item_form.price(class_="input", placeholder=u"฿", onkeyup="update_amount()"),
               item_form.gl.label, item_form.gl(),
               item_form.cost_center.label, item_form.cost_center(),
               item_form.internal_order_code.label, item_form.internal_order_code()
               )

    resp = make_response(form_text)
    if alert:
        resp.headers['HX-Trigger-After-Swap'] = 'delete_warning'
    resp.headers['HX-Trigger-After-Swap'] = 'update_amount'
    return resp


# @receipt_printing.route('/list/receipts', methods=['GET'])
# def list_all_receipts():
#     record = ElectronicReceiptDetail.query.all()
#     return render_template('receipt_printing/list_all_receipts.html', record=record)


sarabun_font = TTFont('Sarabun', 'app/static/fonts/THSarabunNew.ttf')
pdfmetrics.registerFont(sarabun_font)
style_sheet = getSampleStyleSheet()
style_sheet.add(ParagraphStyle(name='ThaiStyle', fontName='Sarabun'))
style_sheet.add(ParagraphStyle(name='ThaiStyleNumber', fontName='Sarabun', alignment=TA_RIGHT))
style_sheet.add(ParagraphStyle(name='ThaiStyleCenter', fontName='Sarabun', alignment=TA_CENTER))


def generate_receipt_pdf(receipt, sign=False, cancel=False):
    logo = Image('app/static/img/logo-MU_black-white-2-1.png', 60, 60)

    digi_name = Paragraph('<font size=12>(ลายมือชื่อดิจิทัล)<br/></font>',
                          style=style_sheet['ThaiStyle']) if sign else ""

    def all_page_setup(canvas, doc):
        canvas.saveState()
        logo_image = ImageReader('app/static/img/mu-watermark.png')
        canvas.drawImage(logo_image, 140, 300, mask='auto')
        canvas.restoreState()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            rightMargin=20,
                            leftMargin=20,
                            topMargin=20,
                            bottomMargin=10,
                            )
    receipt_number = receipt.number
    data = []
    affiliation = '''<para align=center><font size=10>
            คณะเทคนิคการแพทย์ มหาวิทยาลัยมหิดล<br/>
            FACULTY OF MEDICAL TECHNOLOGY, MAHIDOL UNIVERSITY
            </font></para>
            '''
    address = '''<font size=11>
            999 ถ.พุทธมณฑลสาย 4 ต.ศาลายา<br/>
            อ.พุทธมณฑล จ.นครปฐม 73170<br/>
            999 Phutthamonthon 4 Road<br/>
            Salaya, Nakhon Pathom 73170<br/><br/>
            เลขประจำตัวผู้เสียภาษี / Tax ID Number<br/>
            0994000158378
            </font>
            '''

    receipt_info = '''<br/><br/>
            <font size=11>
            เลขที่/No. {receipt_number}<br/>
            วันที่/Date {issued_date}
            </font>
            '''
    issued_date = arrow.get(receipt.created_datetime.astimezone(bangkok)).format(fmt='DD MMMM YYYY', locale='th-th')
    receipt_info_ori = receipt_info.format(receipt_number=receipt_number,
                                           issued_date=issued_date,
                                           )

    header_content_ori = [[Paragraph(address, style=style_sheet['ThaiStyle']),
                           [logo, Paragraph(affiliation, style=style_sheet['ThaiStyle'])],
                           [],
                           Paragraph(receipt_info_ori, style=style_sheet['ThaiStyle'])]]

    header_styles = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ])

    header_ori = Table(header_content_ori, colWidths=[150, 200, 50, 100])

    header_ori.hAlign = 'CENTER'
    header_ori.setStyle(header_styles)

    customer_name = '''<para><font size=12>
            ได้รับเงินจาก / RECEIVED FROM {received_money_from}<br/>
            ที่อยู่ / ADDRESS {address}<br/>
            เลขประจำตัวผู้เสียภาษี / Tax ID Number {taxpayer_dentification_no}
            </font></para>
            '''.format(received_money_from=receipt.received_money_from,
                       address=receipt.received_money_from.address,
                       taxpayer_dentification_no=receipt.received_money_from.taxpayer_dentification_no)

    customer = Table([[Paragraph(customer_name, style=style_sheet['ThaiStyle']),
                       ]],
                     colWidths=[580, 200]
                     )
    customer.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    items = [[Paragraph('<font size=10>ลำดับ / No.</font>', style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>รายการ / Description</font>', style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>จำนวนเงิน / Amount</font>', style=style_sheet['ThaiStyleCenter']),
              ]]
    total = 0
    for n, item in enumerate(receipt.items, start=1):
        item_record = [Paragraph('<font size=12>{}</font>'.format(n), style=style_sheet['ThaiStyleCenter']),
                       Paragraph('<font size=12>{}</font>'.format(item.item), style=style_sheet['ThaiStyle']),
                       Paragraph('<font size=12>{:,.2f}</font>'.format(item.price),
                                 style=style_sheet['ThaiStyleNumber'])
                       ]
        items.append(item_record)
        total += item.price

    n = len(items)
    for i in range(22 - n):
        items.append([
            Paragraph('<font size=12>&nbsp; </font>', style=style_sheet['ThaiStyleNumber']),
            Paragraph('<font size=12> </font>', style=style_sheet['ThaiStyleNumber']),
            Paragraph('<font size=12> </font>', style=style_sheet['ThaiStyleNumber']),
        ])
    total_thai = bahttext(total)
    total_text = "รวมเงินตัวอักษร/ Baht Text : {} รวมเงินทั้งสิ้น/ Total".format(total_thai)
    items.append([
        Paragraph('<font size=12>{}</font>'.format(total_text), style=style_sheet['ThaiStyleNumber']),
        Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
        Paragraph('<font size=12>{:,.2f}</font>'.format(total), style=style_sheet['ThaiStyleNumber'])
    ])
    item_table = Table(items, colWidths=[50, 450, 75])
    item_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
        ('BOX', (0, -1), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (0, -1), 0.25, colors.black),
        ('BOX', (1, 0), (1, -1), 0.25, colors.black),
        ('BOX', (2, 0), (2, -1), 0.25, colors.black),
        ('BOX', (3, 0), (3, -1), 0.25, colors.black),
        ('BOX', (4, 0), (4, -1), 0.25, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, -2), (-1, -2), 10),
    ]))
    item_table.setStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    item_table.setStyle([('SPAN', (0, -1), (1, -1))])

    if receipt.payment_method == 'Cash':
        payment_info = Paragraph('<font size=14>ชำระโดย / PAID BY: เงินสด / CASH</font>',
                                 style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'Credit Card':
        payment_info = Paragraph(
            '<font size=14>ชำระโดย / PAID BY: บัตรเครดิต / CREDIT CARD NUMBER {}-****-****-{} {}</font>'.format(
                receipt.card_number[:4], receipt.card_number[-4:], receipt.bank_name),
            style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == u'QR Payment':
        payment_info = Paragraph('<font size=14>ชำระโดย / PAID BY: สแกนคิวอาร์โค้ด / SCAN QR CODE</font>',
                                 style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'Bank Transfer':
        payment_info = Paragraph(
            '<font size=14>ชำระโดย / PAID BY: โอนผ่านระบบธนาคารอัตโนมัติ / TRANSFER TO BANK</font>',
            style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'Cheque':
        payment_info = Paragraph(
            '<font size=14>ชำระโดย / PAID BY: เช็คสั่งจ่าย / CHEQUE NUMBER {}**** {}</font>'.format(
                receipt.cheque_number[:4], receipt.bank_name),
            style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'Other':
        payment_info = Paragraph(
            '<font size=14>ชำระโดย / PAID BY: วิธีการอื่นๆ / OTHER {}</font>'.format(receipt.other_payment_method),
            style=style_sheet['ThaiStyle'])
    else:
        payment_info = Paragraph('<font size=11>ยังไม่ชำระเงิน / UNPAID</font>', style=style_sheet['ThaiStyle'])

    total_content = [[payment_info,
                      Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                      Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]

    total_table = Table(total_content, colWidths=[360, 150, 50])

    notice_text = '''<para align=center><font size=10>
            กรณีชำระด้วยเช็ค ใบเสร็จรับเงินฉบับนี้จะสมบูรณ์ต่อเมื่อ เรียกเก็บเงินได้ตามเช็คเรียบร้อยแล้ว <br/> If paying by cheque, a receipt will be completed upon receipt of the cheque complete.
            <br/>เอกสารนี้จัดทำด้วยวิธีการทางอิเล็กทรอนิกส์</font></para>
            '''
    notice = Table([[Paragraph(notice_text, style=style_sheet['ThaiStyle'])]])

    sign_text = Paragraph(
        '<br/><font size=12>ผู้รับเงิน / Received by {}<br/></font>'.format(receipt.issuer.personal_info.fullname),
        style=style_sheet['ThaiStyle'])
    receive = [[sign_text,
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]
    receive_officer = Table(receive, colWidths=[0, 80, 20])
    personal_info = [[digi_name,
                      Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]
    issuer_personal_info = Table(personal_info, colWidths=[0, 30, 20])

    position = Paragraph('<font size=12>ตำแหน่ง / Position {}</font>'.format(receipt.issuer.personal_info.position),
                         style=style_sheet['ThaiStyle'])
    position_info = [[position,
                      Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]
    issuer_position = Table(position_info, colWidths=[0, 80, 20])

    cancel_text = '''<para align=right><font size=20 color=red>ยกเลิก {}</font></para>'''.format(receipt.number)
    cancel_receipts = Table([[Paragraph(cancel_text, style=style_sheet['ThaiStyle'])]])
    data.append(KeepTogether(header_ori))
    if receipt.cancelled:
        data.append(KeepTogether(cancel_receipts))
    data.append(KeepTogether(Paragraph('<para align=center><font size=18>ใบเสร็จรับเงิน / RECEIPT<br/><br/></font></para>',
                                   style=style_sheet['ThaiStyle'])))
    data.append(KeepTogether(customer))
    data.append(KeepTogether(Spacer(1, 12)))
    data.append(KeepTogether(Spacer(1, 6)))
    data.append(KeepTogether(item_table))
    data.append(KeepTogether(Spacer(1, 6)))
    data.append(KeepTogether(total_table))
    data.append(KeepTogether(Spacer(1, 12)))
    data.append(KeepTogether(receive_officer))
    data.append(KeepTogether(issuer_personal_info))
    data.append(KeepTogether(issuer_position))
    data.append(KeepTogether(Paragraph('เลขที่กำกับเอกสาร<br/> Regulatory Document No. {}'.format(receipt.number),
                                           style=style_sheet['ThaiStyle'])))
    data.append(KeepTogether(
            Paragraph('Time {} น.'.format(receipt.created_datetime.astimezone(bangkok).strftime('%H:%M:%S')),
                      style=style_sheet['ThaiStyle'])))
    data.append(KeepTogether(notice))
        # data.append(KeepTogether(PageBreak()))
    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup)
    buffer.seek(0)
    return buffer


@receipt_printing.route('/receipts/pdf/<int:receipt_id>', methods=['POST', 'GET'])
def export_receipt_pdf(receipt_id):
    if request.method == 'GET':
        receipt = ElectronicReceiptDetail.query.get(receipt_id)
        if receipt.pdf_file:
            return send_file(BytesIO(receipt.pdf_file), download_name="receipt.pdf", as_attachment=True)
        print(receipt_id)
        buffer = generate_receipt_pdf(receipt)
        return send_file(buffer, download_name="receipt.pdf", as_attachment=True)
    elif request.method == 'POST':
        password = request.form.get('password')
        receipt = ElectronicReceiptDetail.query.get(receipt_id)
        if receipt.pdf_file is None:
            buffer = generate_receipt_pdf(receipt, sign=True)
            sign_pdf = e_sign(buffer, password, include_image=False)
            receipt.pdf_file = sign_pdf.read()
            sign_pdf.seek(0)
            db.session.add(receipt)
            db.session.commit()
        response = make_response()
        response.headers['HX-Refresh'] = 'true'
        return response


@receipt_printing.route('list/receipts/cancel')
def list_to_cancel_receipt():
    record = ElectronicReceiptDetail.query.filter_by(cancelled=True)
    return render_template('receipt_printing/list_to_cancel_receipt.html', record=record)


@receipt_printing.route('/receipts/cancel/confirm/<int:receipt_id>', methods=['GET', 'POST'])
def confirm_cancel_receipt(receipt_id):
    receipt = ElectronicReceiptDetail.query.get(receipt_id)
    if not receipt.cancelled:
        return render_template('receipt_printing/confirm_cancel_receipt.html', receipt=receipt, callback=request.referrer)
    return redirect(url_for('receipt_printing.list_all_receipts'))


@receipt_printing.route('receipts/cancel/<int:receipt_id>', methods=['POST'])
def cancel_receipt(receipt_id):
    receipt = ElectronicReceiptDetail.query.get(receipt_id)
    receipt.cancelled = True
    receipt.cancel_comment = request.form.get('comment')
    buffer = generate_receipt_pdf(receipt)
    receipt.pdf_file = buffer.read()
    db.session.add(receipt)
    db.session.commit()
    return redirect(url_for('receipt_printing.list_to_cancel_receipt'))


@receipt_printing.route('/daily/payment/report', methods=['GET', 'POST'])
def daily_payment_report():
    query = ElectronicReceiptDetail.query
    form = ReportDateForm()
    start_date = None
    end_date = None
    if request.method == 'POST':
        start_date, end_date = form.created_datetime.data.split(' - ')
        start_date = datetime.strptime(start_date, '%d-%m-%Y')
        end_date = datetime.strptime(end_date, '%d-%m-%Y')
        if start_date < end_date:
            query = query.filter(and_(ElectronicReceiptDetail.created_datetime >= start_date,
                                      ElectronicReceiptDetail.created_datetime <= end_date))
        else:
            query = query.filter(cast(ElectronicReceiptDetail.created_datetime, Date) == start_date)
    else:
        flash(form.errors, 'danger')
    start_date = start_date.strftime('%d-%m-%Y') if start_date else ''
    end_date = end_date.strftime('%d-%m-%Y') if end_date else ''
    return render_template('receipt_printing/daily_payment_report.html', records=query, form=form,
                           start_date=start_date, end_date=end_date)


@receipt_printing.route('api/daily/payment/report')
def get_daily_payment_report():
    query = ElectronicReceiptDetail.query
    search = request.args.get('search[value]')
    query = query.filter(db.or_(
        ElectronicReceiptDetail.number.like(u'%{}%'.format(search)),
        ElectronicReceiptDetail.book_number.like(u'%{}%'.format(search))
    ))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        item_data['view'] = '<a href="{}" class="button is-small is-rounded is-info is-outlined">View</a>'.format(
            url_for('receipt_printing.view_daily_payment_report', receipt_id=item.id))
        item_data['created_datetime'] = item_data['created_datetime'].strftime('%d/%m/%Y %H:%M:%S')
        data.append(item_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': ElectronicReceiptDetail.query.count(),
                    'draw': request.args.get('draw', type=int),
                    })


@receipt_printing.route('/payment/report/view/<int:receipt_id>')
def view_daily_payment_report(receipt_id):
    receipt_detail = ElectronicReceiptDetail.query.get(receipt_id)
    return render_template('receipt_printing/view_daily_payment_report.html',
                           receipt_detail=receipt_detail)


@receipt_printing.route('/daily/payment/report/download')
def download_daily_payment_report():
    records = []
    query = ElectronicReceiptDetail.query
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        start_date = datetime.strptime(start_date, '%d-%m-%Y')
        end_date = datetime.strptime(end_date, '%d-%m-%Y')
        if start_date < end_date:
            query = query.filter(and_(ElectronicReceiptDetail.created_datetime >= start_date,
                                      ElectronicReceiptDetail.created_datetime <= end_date))
        else:
            query = query.filter(cast(ElectronicReceiptDetail.created_datetime, Date) == start_date)

    for receipt in query:
        records.append({
            u'เล่มที่': u"{}".format(receipt.book_number),
            u'เลขที่': u"{}".format(receipt.number),
            u'รายการ': u"{}".format(receipt.item_list),
            u'จำนวนเงิน': u"{:,.2f}".format(receipt.paid_amount),
            u'ช่องทางการชำระเงิน': u"{}".format(receipt.payment_method),
            u'เลขที่บัตรเครดิต': u"{}".format(receipt.card_number),
            u'เลขที่เช็ค': u"{}".format(receipt.cheque_number),
            u'ธนาคาร': u"{}".format(receipt.bank_name),
            u'ชื่อผู้ชำระเงิน': u"{}".format(receipt.received_money_from),
            u'ผู้รับเงิน/ผู้บันทึก': u"{}".format(receipt.issuer.personal_info.fullname),
            u'ตำแหน่ง': u"{}".format(receipt.issuer.personal_info.position),
            u'วันที่': u"{}".format(receipt.created_datetime.strftime('%d/%m/%Y %H:%M:%S')),
            u'หมายเหตุ': u"{}".format(receipt.comment),
            u'GL': u"{}".format(receipt.item_gl_list if receipt and receipt.item_gl_list else ''),
            u'Cost Center': u"{}".format(receipt.item_cost_center_list if receipt and receipt.item_cost_center_list else ''),
            u'IO': u"{}".format(receipt.item_internal_order_list if receipt and receipt.item_internal_order_list else '')
        })
    df = DataFrame(records)
    for idx in range(0, len(df)):  # in case there's more than 1 row with '\n'
        try:
            if '\n' in df['รายการ'][idx]:  # step1 check for '\n'
                newIdx = idx + 0.5
                df.loc[newIdx] = df.loc[idx]  # step2 add new row

                # step3 split value before/after '\n'
                # fix values in 'รายการ'
                strSplit = df['รายการ'][idx].split('\n')
                df['รายการ'][idx] = strSplit[0]
                df['รายการ'][newIdx] = strSplit[1]

                # fix values in 'GL'
                strSplit = df['GL'][idx].split('\n')
                df['GL'][idx] = strSplit[0]
                df['GL'][newIdx] = strSplit[1]

                # fix values in 'Cost Center'
                strSplit = df['Cost Center'][idx].split('\n')
                df['Cost Center'][idx] = strSplit[0]
                df['Cost Center'][newIdx] = strSplit[1]

                # fix values in 'IO'
                strSplit = df['IO'][idx].split('\n')
                df['IO'][idx] = strSplit[0]
                df['IO'][newIdx] = strSplit[1]
        except:
            continue  # to ignore NaN
    df = df.sort_index().reset_index(drop=True)
    df.to_excel('daily_payment_report.xlsx')
    return send_file(os.path.join(os.getcwd(),'daily_payment_report.xlsx'))


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


@receipt_printing.route('receipt/new/require/<int:receipt_id>', methods=['GET', 'POST'])
def require_new_receipt(receipt_id):
    form = ReceiptRequireForm()
    receipt = ElectronicReceiptDetail.query.get(receipt_id)
    if request.method == 'POST':
        filename = ''
        receipt_require = ElectronicReceiptRequest()
        form.populate_obj(receipt_require)
        receipt_require.staff = current_user
        receipt_require.detail = receipt
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
                except:
                    flash('Failed to upload the attached file to the Google drive.', 'danger')
                else:
                    flash('The attached file has been uploaded to the Google drive', 'success')
                    receipt_require.url_drive = file_drive['id']

        db.session.add(receipt_require)
        db.session.commit()
        title = u'แจ้งเตือนคำร้องขอออกใบเสร็จใหม่ {}'.format(receipt_require.detail.number)
        message = u'เรียน คุณพิชญาสินี\n\n ขออนุมัติคำร้องขอออกใบเสร็จเลขที่ {} เล่มที่ {} เนื่องจาก {}' \
            .format(receipt_require.detail.number, receipt_require.detail.book_number, receipt_require.reason)
        message += u'\n\n======================================================'
        message += u'\nอีเมลนี้ส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ ' \
                   u'หากมีปัญหาใดๆเกี่ยวกับเว็บไซต์กรุณาติดต่อ yada.boo@mahidol.ac.th หน่วยข้อมูลและสารสนเทศ '
        message += u'\nThis email was sent by an automated system. Please do not reply.' \
                   u' If you have any problem about website, please contact the IT unit.'
        send_mail([u'pichayasini.jit@mahidol.ac.th'], title, message)
        flash(u'บันทึกข้อมูลสำเร็จ.', 'success')
        return render_template('receipt_printing/list_to_require_receipt.html')
        # Check Error
    else:
        for er in form.errors:
            flash(er, 'danger')
    return render_template('receipt_printing/require_new_receipt.html', form=form, receipt=receipt)


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scopes)
    return GoogleDrive(gauth)


@receipt_printing.route('/receipt/require/list')
def list_to_require_receipt():
    return render_template('receipt_printing/list_to_require_receipt.html')


@receipt_printing.route('/api/data/require')
def get_require_receipt_data():
    query = ElectronicReceiptDetail.query.filter_by(cancelled=True)
    search = request.args.get('search[value]')
    query = query.filter(db.or_(
        ElectronicReceiptDetail.number.like(u'%{}%'.format(search)),
        ElectronicReceiptDetail.book_number.like(u'%{}%'.format(search))
    ))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for r in query:
        record_data = r.to_dict()
        record_data['created_datetime'] = record_data['created_datetime'].strftime('%d/%m/%Y %H:%M:%S')
        record_data['require_receipt'] = '<a href="{}"><i class="fas fa-receipt"></i></a>'.format(
            url_for('receipt_printing.require_new_receipt', receipt_id=r.id))
        record_data['cancelled'] = '<i class="fas fa-times has-text-danger"></i>' if r.cancelled else '<i class="far fa-check-circle has-text-success"></i>'
        record_data['view_require_receipt'] = '<a href="{}"><i class="fas fa-eye"></i></a>'.format(
            url_for('receipt_printing.view_require_receipt', receipt_id=r.id))
        data.append(record_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': ElectronicReceiptDetail.query.count(),
                    'draw': request.args.get('draw', type=int),
                    })


@receipt_printing.route('/receipt/require/list/view')
@login_required
@finance_head_permission.require()
def view_require_receipt():
    request_receipt = ElectronicReceiptRequest.query.all()
    return render_template('receipt_printing/view_require_receipt.html',
                           request_receipt=request_receipt)


@receipt_printing.route('/receipt-data/')
def view_receipt_by_list_type():
    list_type = request.args.get('list_type')
    return render_template('receipt_printing/list_all_receipts.html', list_type=list_type)


@receipt_printing.route('api/receipt-data/all')
def get_receipt_by_list_type():
    list_type = request.args.get('list_type')
    query = ElectronicReceiptDetail.query
    org = current_user.personal_info.org

    if list_type is None:
        query = query.filter_by(issuer_id=current_user.id)

    search = request.args.get('search[value]')
    col_idx = request.args.get('order[0][column]')
    direction = request.args.get('order[0][dir]')
    col_name = request.args.get('columns[{}][data]'.format(col_idx))
    query = query.filter(db.or_(
        ElectronicReceiptDetail.number.ilike(u'%{}%'.format(search)),
        ElectronicReceiptDetail.comment.ilike(u'%{}%'.format(search))
    ))
    column = getattr(ElectronicReceiptDetail, col_name)
    if direction == 'desc':
        column = column.desc()
    query = query.order_by(column)
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    if list_type == 'org':
        query = query.filter(ElectronicReceiptDetail.issuer.has(StaffAccount.personal_info.has(org_id=org.id)))
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []

    for item in query:
        item_data = item.to_dict()
        item_data['preview'] = '<a href="{}" class="button is-small is-rounded is-info is-outlined">Preview</a>'.format(
            url_for('receipt_printing.show_receipt_detail', receipt_id=item.id))
        item_data['created_datetime'] = item_data['created_datetime'].strftime('%d/%m/%Y %H:%M:%S')
        item_data['status'] = '<i class="fas fa-times has-text-danger"></i>' if item.cancelled else '<i class="far fa-check-circle has-text-success"></i>'
        item_data['issuer'] = item_data['issuer']
        item_data['item_list'] = item_data['item_list']
        data.append(item_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': ElectronicReceiptDetail.query.count(),
                    'draw': request.args.get('draw', type=int),
                    })


@receipt_printing.route('/receipt/detail/show/<int:receipt_id>', methods=['GET', 'POST'])
def show_receipt_detail(receipt_id):
    receipt = ElectronicReceiptDetail.query.get(receipt_id)
    total = sum([t.price for t in receipt.items])
    total_thai = bahttext(total)
    return render_template('receipt_printing/receipt_detail.html',
                           receipt=receipt,
                           total=total,
                           total_thai=total_thai,
                           enumerate=enumerate)


@receipt_printing.route('/io_code_and_cost_center/select')
@finance_head_permission.require()
def select_btw_io_code_and_cost_center():
    return render_template('receipt_printing/select_io_code_and_cost_center.html', name=current_user)


@receipt_printing.route('/cost_center/show')
def show_cost_center():
    cost_center = CostCenter.query.all()
    return render_template('receipt_printing/show_cost_center.html', cost_center=cost_center, url_back=request.referrer)


@receipt_printing.route('/io_code/show')
def show_io_code():
    io_code = IOCode.query.all()
    return render_template('receipt_printing/show_io_code.html', io_code=io_code, url_back=request.referrer)


@receipt_printing.route('/cost_center/new', methods=['POST', 'GET'])
def new_cost_center():
    form = CostCenterForm()
    if form.validate_on_submit():
        cost_center_detail = CostCenter()
        cost_center_detail.id = form.cost_center.data
        db.session.add(cost_center_detail)
        db.session.commit()
        flash(u'บันทึกเรียบร้อย.', 'success')
        return redirect(url_for('receipt_printing.show_cost_center'))
    # Check Error
    else:
        for er in form.errors:
            flash("{}:{}".format(er, form.errors[er]), 'danger')
    return render_template('receipt_printing/new_cost_center.html', form=form, url_callback=request.referrer)


@receipt_printing.route('/io_code/new', methods=['POST', 'GET'])
def new_IOCode():
    form = IOCodeForm()
    if form.validate_on_submit():
        IOCode_detail = IOCode()
        IOCode_detail.id = form.io.data
        IOCode_detail.mission = form.mission.data
        IOCode_detail.name = form.name.data
        IOCode_detail.org = form.org.data
        db.session.add(IOCode_detail)
        db.session.commit()
        flash(u'บันทึกเรียบร้อย.', 'success')
        return redirect(url_for('receipt_printing.show_io_code'))
    # Check Error
    else:
        for er in form.errors:
            flash("{}:{}".format(er, form.errors[er]), 'danger')
    return render_template('receipt_printing/new_IOCode.html', form=form, url_callback=request.referrer)


@receipt_printing.route('/io_code/<string:iocode_id>/change-active-status')
def io_code_change_active_status(iocode_id):
    iocode_query = IOCode.query.filter_by(id=iocode_id).first()
    iocode_query.is_active = True if not iocode_query.is_active else False
    db.session.add(iocode_query)
    db.session.commit()
    flash(u'แก้ไขสถานะเรียบร้อยแล้ว', 'success')
    return redirect(url_for('receipt_printing.show_io_code'))


@receipt_printing.route('/api/received_money_from/address')
def get_received_money_from_by_payer_id():
    payer_id = request.args.get('payer_id', type=int)
    payer = ElectronicReceiptReceivedMoneyFrom.query.get(payer_id)
    return jsonify({'address': payer.address})


@receipt_printing.route('/info/payer/add', methods=['GET', 'POST'])
@login_required
def add_info_payer_ref():
    form = ReceiptInfoPayerForm()
    if request.method == 'POST':
       new_info_payer = ElectronicReceiptReceivedMoneyFrom()
       form.populate_obj(new_info_payer)
       db.session.add(new_info_payer)
       db.session.commit()
       flash('New information payer has been added.', 'success')
       return redirect(url_for('receipt_printing.view_info_payer'))
    return render_template('receipt_printing/info_payer_ref.html', form=form, url_callback=request.referrer)


@receipt_printing.route('/receipt/information-payer/list')
def view_info_payer():
    return render_template('receipt_printing/view_info_payer.html')


@receipt_printing.route('/api/data/info-payer')
def get_info_payer_data():
    query = ElectronicReceiptReceivedMoneyFrom.query
    search = request.args.get('search[value]')
    query = query.filter(db.or_(
        ElectronicReceiptReceivedMoneyFrom.received_money_from.like(u'%{}%'.format(search)),
        ElectronicReceiptReceivedMoneyFrom.address.like(u'%{}%'.format(search))
    ))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for payer_info in query:
        record_data = payer_info.to_dict()
        record_data['edit'] = '<a href="{}" class="button is-small is-rounded is-info is-outlined">Edit</a>'.format(
            url_for('receipt_printing.edit_info_payer', payer_info_id=payer_info.id))
        data.append(record_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': ElectronicReceiptReceivedMoneyFrom.query.count(),
                    'draw': request.args.get('draw', type=int),
                    })


@receipt_printing.route('/information/payer<int:payer_info_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_info_payer(payer_info_id):
    payer_info = ElectronicReceiptReceivedMoneyFrom.query.get(payer_info_id)
    form = ReceiptInfoPayerForm(obj=payer_info)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(payer_info)
            db.session.add(payer_info)
            db.session.commit()
            flash(u'แก้ไขข้อมูลเรียบร้อย', 'success')
        return redirect(url_for('receipt_printing.view_info_payer', payer_info_id=payer_info_id))
    return render_template('receipt_printing/edit_info_payer.html', payer_info_id=payer_info_id, form=form)


@receipt_printing.route('receipt/<int:receipt_id>/password/enter', methods=['GET', 'POST'])
@login_required
def enter_password_for_sign_digital(receipt_id):
    form = PasswordOfSignDigitalForm()
    return render_template('receipt_printing/password_modal.html', form=form, receipt_id=receipt_id)



