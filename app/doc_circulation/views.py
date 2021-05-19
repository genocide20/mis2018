# -*- coding:utf-8 -*-
import os
import datetime

import requests
from werkzeug.utils import secure_filename

from . import docbp
from flask_login import current_user
from flask import render_template, url_for, request, flash, redirect, jsonify
from models import *
from pytz import timezone
from forms import *
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive
from app.models import Org


bkk = timezone('Asia/Bangkok')

# TODO: folder ID should be stored in the Org model to organize files by organization

FOLDER_ID = '1832el0EAqQ6NVz2wB7Ade6wRe-PsHQsu'

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scopes)
    return GoogleDrive(gauth)


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

@docbp.route('/')
def index():
    rounds = DocRound.query.all()
    return render_template('documents/index.html', rounds=rounds)


@docbp.route('/admin/rounds/<int:round_id>/documents')
def admin_view_round(round_id):
    round = DocRound.query.get(round_id)
    return render_template('documents/admin/docs.html', round=round)


@docbp.route('/rounds/<int:round_id>/documents')
def view_round(round_id):
    round = DocRound.query.get(round_id)
    records = []
    for doc in round.documents.all():
        for rec in doc.recv_records:
            if rec.staff == current_user:
                records.append(rec)
    return render_template('documents/round.html', round=round, records=records)


@docbp.route('/documents/<int:rec_id>')
def view_recv_record(rec_id):
    rec = DocReceiveRecord.query.get(rec_id)
    return render_template('documents/recv_record.html', rec=rec)


@docbp.route('/admin')
def admin_index():
    rounds = DocRound.query.all()
    return render_template('documents/admin/index.html', rounds=rounds)


@docbp.route('/admin/rounds', methods=['GET', 'POST'])
def add_round():
    form = RoundForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_round = DocRound()
            form.populate_obj(new_round)
            new_round.creator = current_user
            db.session.add(new_round)
            db.session.commit()
            flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
            return redirect(url_for('doc.admin_index'))
        else:
            for err in form.errors:
                flash('{}'.format(err), 'danger')
    return render_template('documents/admin/round_form.html', form=form)


@docbp.route('/admin/rounds/<int:round_id>/docs/<int:doc_id>', methods=['GET', 'POST'])
@docbp.route('/admin/rounds/<int:round_id>/docs', methods=['GET', 'POST'])
def add_document(round_id, doc_id=None):
    if doc_id:
        doc = DocDocument.query.get(doc_id)
        form = DocumentForm(obj=doc)
    else:
        form = DocumentForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not doc_id:
                new_doc = DocDocument()
                new_doc.stage = 'drafting'
                filename = ''
                fileurl = ''
            else:
                new_doc = doc
                filename = doc.file_name
                fileurl = doc.url
            form.populate_obj(new_doc)
            new_doc.round_id = round_id
            if not new_doc.addedAt:
                new_doc.addedAt = bkk.localize(datetime.datetime.now())
            new_doc.deadline = bkk.localize(new_doc.deadline)
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
                        new_doc.url = file_drive['id']
                        new_doc.file_name = filename
            else:
                new_doc.file_name = filename
                new_doc.url = fileurl
            db.session.add(new_doc)
            db.session.commit()
            if doc_id:
                flash('The document has been updated.', 'success')
            else:
                flash('New document has been added.', 'success')
            return redirect(url_for('doc.admin_view_round', round_id=round_id))
        else:
            for field, err in form.errors.items():
                flash('{} {}'.format(field, err), 'danger')
    return render_template('documents/admin/document_form.html', form=form, round_id=round_id)


@docbp.route('/admin/docs/<int:doc_id>/send', methods=['GET', 'POST'])
def send_document(doc_id):
    doc = DocDocument.query.get(doc_id)
    if doc:
        doc.stage = 'ready'
        db.session.add(doc)
        db.session.commit()
        flash('The document is ready to be reviewed.', 'success')
        return redirect(url_for('doc.admin_view_round', round_id=doc.round_id))
    else:
        flash('The document has been not been found.', 'danger')
        return redirect(url_for('doc.admin_index'))


@docbp.route('/admin/rounds/<int:round_id>/send_for_review', methods=['GET', 'POST'])
def send_round_for_review(round_id):
    form = RoundSendForm()
    select_orgs = (4, 6, 7, 8, 10)
    form.targets.choices = [(org.id, org.name) for org in Org.query.all() if org.id in select_orgs]
    form.targets.data = [current_user.personal_info.org.id]
    if request.method == 'POST':
        if form.validate_on_submit():
            for target_id in form.targets.data:
                send_record = DocRoundOrg(
                    org_id=target_id,
                    round_id=round_id,
                    sent_at=bkk.localize(datetime.datetime.now())
                )
                db.session.add(send_record)
            db.session.commit()
            flash('The documents have been sent to the department for a review.', 'success')
            return redirect(url_for('doc.admin_index'))
        else:
            for field, error in form.errors:
                flash('{} {}'.format(field, error), 'danger')
    return render_template('documents/admin/send_for_review.html', form=form, round_id=round_id)


@docbp.route('/head/rounds/<int:round_id>/documents')
def head_view_docs(round_id):
    _org = current_user.personal_info.org
    if _org.head == current_user.email:
        sent_round = DocRoundOrg.query.filter_by(org_id=_org.id, round_id=round_id).first()
        return render_template('documents/head/docs.html', sent_round=sent_round)
    return u'You do have a permission to review documents targeted for this {}.'.format(_org.name)


@docbp.route('/head/rounds')
def head_view_rounds():
    _org = current_user.personal_info.org
    if _org.head == current_user.email:
        sent_rounds = DocRoundOrg.query.filter_by(org_id=_org.id).all()
        return render_template('documents/head/rounds.html', sent_rounds=sent_rounds)


@docbp.route('/head/sent_rounds/<int:sent_round_org_id>/docs/<int:doc_id>/review', methods=['GET', 'POST'])
def head_review(doc_id, sent_round_org_id):
    doc = DocDocument.query.get(doc_id)
    if current_user.email == current_user.personal_info.org.head:
        _DocumentReceiptForm = create_doc_receipt_form(current_user.personal_info.org)
        form = _DocumentReceiptForm()
        if request.method == 'POST':
            if form.validate_on_submit():
                receipt = DocReceiveRecord()
                form.populate_obj(receipt)
                receipt.round_org_id = sent_round_org_id
                receipt.doc = doc
                receipt.sender = current_user
                receipt.sent_at = bkk.localize(datetime.datetime.now())
                db.session.add(receipt)
                db.session.commit()
                flash('The document has been sent to the members.', 'success')
                return redirect(url_for('doc.head_view_docs', round_id=doc.round_id))
            else:
                for field, err in form.errors.items():
                    flash('{} {}'.format(field, err), 'danger')
        return render_template('documents/head/review.html', form=form, doc=doc)