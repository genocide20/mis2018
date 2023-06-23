# -*- coding:utf-8 -*-
import datetime
import pytz
import arrow
from sqlalchemy import and_
from . import pa_blueprint as pa

from app.roles import hr_permission, manager_permission
from ..models import Org
from app.PA.forms import *

tz = pytz.timezone('Asia/Bangkok')

from flask import render_template, flash, redirect, url_for, make_response, request
from flask_login import login_required, current_user


@pa.route('/user-performance')
@login_required
def user_performance():
    staff_personal = PAAgreement.query.all()
    rounds = PARound.query.all()
    return render_template('pa/user_performance.html', staff_personal=staff_personal,
                           name=current_user, rounds=rounds)


@pa.route('/rounds/<int:round_id>/items/add', methods=['GET', 'POST'])
@pa.route('/rounds/<int:round_id>/pa/<int:pa_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def add_pa_item(round_id, item_id=None, pa_id=None):
    pa_round = PARound.query.get(round_id)
    categories = PAItemCategory.query.all()
    if pa_id:
        pa = PAAgreement.query.get(pa_id)
    else:
        pa = PAAgreement.query.filter_by(round_id=round_id,
                                         staff=current_user).first()
    if pa is None:
        pa = PAAgreement(round_id=round_id,
                         staff=current_user,
                         created_at=arrow.now('Asia/Bangkok').datetime)
        db.session.add(pa)
        db.session.commit()

    if item_id:
        pa_item = PAItem.query.get(item_id)
        form = PAItemForm(obj=pa_item)
    else:
        pa_item = None
        form = PAItemForm()

    for kpi in pa.kpis:
        items = []
        default = None
        for item in kpi.pa_kpi_items:
            items.append((item.id, item.goal))
            if pa_item:
                if item in pa_item.kpi_items:
                    default = item.id
        field_ = form.kpi_items_.append_entry(default)
        field_.choices = [('', 'ไม่ระบุเป้าหมาย')] + items
        field_.label = kpi.detail

    if form.validate_on_submit():
        for i in range(len(pa.kpis)):
            form.kpi_items_.pop_entry()

        if not pa_item:
            pa_item = PAItem()
        form.populate_obj(pa_item)
        new_kpi_items = []
        for e in form.kpi_items_.entries:
            if e.data:
                kpi_item = PAKPIItem.query.get(int(e.data))
                if kpi_item:
                    new_kpi_items.append(kpi_item)
        pa_item.kpi_items = new_kpi_items
        pa.pa_items.append(pa_item)
        pa.updated_at = arrow.now('Asia/Bangkok').datetime
        db.session.add(pa_item)
        db.session.commit()
        flash('เพิ่มรายละเอียดภาระงานเรียบร้อย', 'success')
        return redirect(url_for('pa.add_pa_item', round_id=round_id))
    else:
        for er in form.errors:
            flash("{}:{}".format(er, form.errors[er]), 'danger')
    return render_template('pa/pa_item_edit.html',
                           form=form,
                           pa_round=pa_round,
                           pa=pa,
                           pa_item_id=item_id,
                           categories=categories)


@pa.route('/pa/<int:pa_id>/kpis/add', methods=['GET', 'POST'])
@login_required
def add_kpi(pa_id):
    round_id = request.args.get('round_id', type=int)
    form = PAKPIForm()
    if form.validate_on_submit():
        new_kpi = PAKPI()
        form.populate_obj(new_kpi)
        new_kpi.pa_id = pa_id
        db.session.add(new_kpi)
        db.session.commit()
        flash('เพิ่มรายละเอียดเกณฑ์การประเมินเรียบร้อย', 'success')
        return redirect(url_for('pa.add_kpi'), pa_id=pa_id)
    else:
        for er in form.errors:
            flash("{}:{}".format(er, form.errors[er]), 'danger')
    return render_template('pa/add_kpi.html', form=form, round_id=round_id, pa_id=pa_id)


@pa.route('/staff/rounds/<int:round_id>/task/view')
@login_required
def view_pa_item(round_id):
    round = PARound.query.get(round_id)
    agreement = PAAgreement.query.all()
    return render_template('pa/view_task.html', round=round, agreement=agreement)


@pa.route('/pa/')
@login_required
def index():
    #TODO: create head committee permission for access special part
    return render_template('pa/index.html', hr_permission=hr_permission, manager_permission=manager_permission)


@pa.route('/hr/create-round', methods=['GET', 'POST'])
@login_required
def create_round():
    pa_round = PARound.query.all()
    if request.method == 'POST':
        form = request.form
        start_d, end_d = form.get('dates').split(' - ')
        start = datetime.datetime.strptime(start_d, '%d/%m/%Y')
        end = datetime.datetime.strptime(end_d, '%d/%m/%Y')
        createround = PARound(
            start=tz.localize(start),
            end=tz.localize(end)
        )
        db.session.add(createround)
        db.session.commit()
        flash('เพิ่มรอบการประเมินใหม่เรียบร้อยแล้ว', 'success')
        return redirect(url_for('pa.create_round'))
    return render_template('pa/hr_create_round.html', pa_round=pa_round)


@pa.route('/hr/add-committee', methods=['GET', 'POST'])
@login_required
def add_commitee():
    form = PACommitteeForm()
    if form.validate_on_submit():
        commitee = PACommittee()
        form.populate_obj(commitee)
        db.session.add(commitee)
        db.session.commit()
        flash('เพิ่มผู้ประเมินใหม่เรียบร้อยแล้ว', 'success')
    else:
        for err in form.errors:
            flash('{}: {}'.format(err, form.errors[err]), 'danger')
    return render_template('pa/hr_add_committee.html', form=form)


@pa.route('/hr/committee', methods=['GET', 'POST'])
@login_required
def show_commitee():
    # TODO: org filter
    org_id = request.args.get('deptid')
    departments = Org.query.all()
    if org_id is None:
        committee_list = PACommittee.query.all()
    else:
        committee_list = PACommittee.query.filter(PACommittee.has(org_id=org_id))
    return render_template('pa/hr_show_committee.html',
                           sel_dept=org_id, committee_list=committee_list,
                           departments=[{'id': d.id, 'name': d.name} for d in departments])


@pa.route('/pa/<int:pa_id>/requests', methods=['GET', 'POST'])
def create_request(pa_id):
    pa = PAAgreement.query.get(pa_id)
    form = PARequestForm()
    supervisor_email = current_user.personal_info.org.head or current_user.personal_info.org.parent.head
    supervisor = StaffAccount.query.filter_by(email=supervisor_email).first()
    if form.validate_on_submit():
        new_request = PARequest()
        form.populate_obj(new_request)
        new_request.pa_id = pa_id
        right_now = arrow.now('Asia/Bangkok').datetime
        new_request.created_at = right_now
        new_request.submitted_at = right_now
        new_request.supervisor = supervisor
        db.session.add(new_request)
        db.session.commit()
        flash('ส่งคำขอเรียบร้อยแล้ว', 'success')
        return redirect(url_for('pa.add_pa_item', round_id=pa.round_id))
    return render_template('PA/request_form.html', form=form, pa=pa)


@pa.route('/head/requests')
@login_required
def all_request():
    all_req = PARequest.query.filter_by(supervisor_id=current_user.id).filter(PARequest.submitted_at != None).all()
    return render_template('pa/head_all_request.html', all_req=all_req)


@pa.route('/head/request/<int:request_id>/detail')
@login_required
def view_request(request_id):
    categories = PAItemCategory.query.all()
    req = PARequest.query.get(request_id)
    return render_template('PA/head_respond_request.html',
                           categories=categories, req=req)


@pa.route('/head/request/<int:request_id>', methods=['GET', 'POST'])
@login_required
def respond_request(request_id):
    #TODO: protect button assign committee in template when created committees list(in paagreement)
    req = PARequest.query.get(request_id)
    if request.method == 'POST':
        form = request.form
        req.status = form.get('approval')
        if req.for_ == 'ขอรับรอง':
            req.pa.approved_at = arrow.now('Asia/Bangkok').datetime
        elif req.for_ == 'ขอแก้ไข':
            req.pa.approved_at = None
        #TODO: recheck arrow.now datetime
        req.responded_at = arrow.now('Asia/Bangkok').datetime
        req.supervisor_comment = form.get('supervisor_comment')
        db.session.add(req)
        db.session.commit()
        flash('ดำเนินการอนุมัติเรียบร้อยแล้ว', 'success')
    return redirect(url_for('pa.all_request'))


@pa.route('/head/create-scoresheet/<int:pa_id>', methods=['GET', 'POST'])
@login_required
def create_scoresheet(pa_id):
    scoresheet = PAScoreSheet.query.filter_by(pa_id=pa_id).filter(PACommittee.staff == current_user).first()
    pa = PAAgreement.query.filter_by(id=pa_id).first()
    committee = PACommittee.query.filter_by(org=pa.staff.personal_info.org, role='ประธานกรรมการ').first()
    print(committee.staff.id)
    if not scoresheet:
        create_score_sheet = PAScoreSheet(
            pa_id=pa_id,
            committee_id=committee.id
        )
        db.session.add(create_score_sheet)
        db.session.commit()

        pa_item = PAItem.query.filter_by(pa_id=pa_id).all()
        for item in pa_item:
            for kpi_item in item.kpi_items:
                create_score_sheet_item = PAScoreSheetItem(
                        score_sheet_id=create_score_sheet.id,
                        item_id=item.id,
                        kpi_item_id=kpi_item.id
                    )
                db.session.add(create_score_sheet_item)
                db.session.commit()
        return redirect(url_for('pa.all_performance', scoresheet_id=create_score_sheet.id))
    else:
        return render_template('pa/eva_all_performance.html', scoresheet=scoresheet)


@pa.route('/head/create-scoresheet/<int:pa_id>/for-committee', methods=['GET', 'POST'])
@login_required
def create_scoresheet_for_committee(pa_id):
    pa = PAAgreement.query.get(pa_id)
    for c in pa.committees:
        scoresheet = PAScoreSheet.query.filter_by(pa_id=pa_id, committee_id=c.id).first()
        if not scoresheet:
            create_scoresheet = PAScoreSheet(
                pa_id=pa_id,
                committee_id=c.id
            )
            db.session.add(create_scoresheet)
            db.session.commit()
            pa_item = PAItem.query.filter_by(pa_id=pa_id).all()
            for item in pa_item:
                for kpi_item in item.kpi_items:
                    create_scoresheet_item = PAScoreSheetItem(
                        score_sheet_id=create_scoresheet.id,
                        item_id=item.id,
                        kpi_item_id=kpi_item.id
                    )
                    db.session.add(create_scoresheet_item)
                    db.session.commit()
        flash('มีการเพิ่มผู้ประเมินเรียบร้อยแล้ว', 'success')
    flash('ส่งการประเมินไปยังกลุ่มผู้ประเมินเรียบร้อยแล้ว', 'success')
    return redirect(url_for('pa.all_approved_pa'))


@pa.route('/head/assign-committee/<int:pa_id>', methods=['GET', 'POST'])
@login_required
def assign_committee(pa_id):
    pa = PAAgreement.query.filter_by(id=pa_id).first()
    committee = PACommittee.query.filter_by(round_id=pa.round_id, org=pa.staff.personal_info.org).filter(
        PACommittee.staff != current_user).all()
    if request.method == 'POST':
        form = request.form
        pa.committees = []
        for c_id in form.getlist("commitees"):
            committee = PACommittee.query.get(int(c_id))
            pa.committees.append(committee)
            db.session.add(committee)
            db.session.commit()
        flash('บันทึกกลุ่มผู้ประเมินเรียบร้อยแล้ว', 'success')
        return redirect(url_for('pa.all_approved_pa'))
    return render_template('pa/head_assign_committee.html', pa=pa, committee=committee)


@pa.route('/head/all-approved-pa')
@login_required
def all_approved_pa():
    #TODO: In template, disable create scoresheet for committee when it already created
    pa = PAAgreement.query.filter(and_(PARequest.submitted_at is not None,
                                       PARequest.for_ == 'ขอรับการประเมิน',
                                       PARequest.supervisor_id == current_user.id)).all()
    return render_template('pa/head_all_approved_pa.html', pa=pa)


@pa.route('/head/all-approved-pa/summary-scoresheet/<int:pa_id>', methods=['GET', 'POST'])
@login_required
def summary_scoresheet(pa_id):
    #TODO: fixed position of item
    #TODO: show evaluation score of each committees
    pa = PAAgreement.query.filter_by(id=pa_id).first()
    committee = PACommittee.query.filter_by(org=pa.staff.personal_info.org, role='ประธานกรรมการ').first()
    consolidated_score_sheet = PAScoreSheet.query.filter_by(pa_id=pa_id, is_consolidated=True).filter(PACommittee.staff == current_user).first()
    if consolidated_score_sheet:
        score_sheet_items = PAScoreSheetItem.query.filter_by(score_sheet_id=consolidated_score_sheet.id).all()
    else:
        consolidated_score_sheet = PAScoreSheet(
            pa_id=pa_id,
            committee_id=committee.id,
            is_consolidated=True
        )
        db.session.add(consolidated_score_sheet)
        db.session.commit()

        pa_items = PAItem.query.filter_by(pa_id=pa_id).all()
        for item in pa_items:
            for kpi_item in item.kpi_items:
                consolidated_score_sheet_item = PAScoreSheetItem(
                    score_sheet_id=consolidated_score_sheet.id,
                    item_id=item.id,
                    kpi_item_id=kpi_item.id
                )
                db.session.add(consolidated_score_sheet_item)
                db.session.commit()
        score_sheet_items = PAScoreSheetItem.query.filter_by(score_sheet_id=consolidated_score_sheet.id).all()

    if request.method == 'POST':
        form = request.form
        for field, value in form.items():
            if field.startswith('pa-item-'):
                pa_item_id, kpi_item_id = field.split('-')[-2:]
                scoresheet_item = consolidated_score_sheet.score_sheet_items\
                    .filter_by(item_id=int(pa_item_id), kpi_item_id=int(kpi_item_id)).first()
                scoresheet_item.score = float(value)
                db.session.add(scoresheet_item)
        db.session.commit()
        flash('บันทึกผลค่าเฉลี่ยเรียบร้อยแล้ว', 'success')
    return render_template('pa/head_summary_score.html',
                           score_sheet_items=score_sheet_items,
                           consolidated_score_sheet=consolidated_score_sheet)


@pa.route('/confirm-score/<int:scoresheet_id>')
@login_required
def confirm_score(scoresheet_id):
    scoresheet = PAScoreSheet.query.filter_by(id=scoresheet_id).first()
    scoresheet.is_final = True
    db.session.add(scoresheet)
    db.session.commit()
    flash('บันทึกคะแนนเรียบร้อยแล้ว', 'success')
    return redirect(request.referrer)


@pa.route('/eva/rate_performance/<int:scoresheet_id>', methods=['GET', 'POST'])
@login_required
def rate_performance(scoresheet_id):
    scoresheet = PAScoreSheet.query.get(scoresheet_id)
    pa = PAAgreement.query.get(scoresheet.pa_id)
    head_scoresheet = pa.pa_score_sheet.filter(PACommittee.role == 'ประธานกรรมการ',
                                               PAScoreSheet.is_consolidated == False).first()
    if request.method == 'POST':
        form = request.form
        for field, value in form.items():
            if field.startswith('pa-item-'):
                scoresheet_item_id = field.split('-')[-1]
                scoresheet_item = PAScoreSheetItem.query.get(scoresheet_item_id)
                scoresheet_item.score = float(value)
                db.session.add(scoresheet_item)
        db.session.commit()
        flash('ส่งผลประเมินไปยังประธานกรรมเรียบร้อยแล้ว', 'success')
    return render_template('pa/eva_rate_performance.html', scoresheet=scoresheet, head_scoresheet=head_scoresheet)


@pa.route('/eva/all_performance/<int:scoresheet_id>')
@login_required
def all_performance(scoresheet_id):
    scoresheet = PAScoreSheet.query.filter_by(id=scoresheet_id).first()
    return render_template('pa/eva_all_performance.html', scoresheet=scoresheet)


@pa.route('/eva/create-consensus-scoresheets/<int:pa_id>')
@login_required
def create_consensus_scoresheets(pa_id):
    # TODO: recheck bug
    pa = PAAgreement.query.filter_by(id=pa_id).first()
    scoresheet = PAScoreSheet.query.filter_by(pa_id=pa_id, is_consolidated=True, is_final=True).first()
    for c in pa.committees:
        create_approvescore = PAApprovedScoreSheet(
            score_sheet_id=scoresheet.id,
            committee_id=c.id
        )
        db.session.add(create_approvescore)
        db.session.commit()
    return redirect(url_for('pa.all_approved_pa'))


@pa.route('/eva/consensus-scoresheets')
@login_required
def consensus_scoresheets():
    # TODO: recheck bug
    committee = PACommittee.query.filter_by(staff=current_user).all()
    for c in committee:
        approved_scoresheets = PAApprovedScoreSheet.query.filter_by(committee_id=c.id).all()
    if not committee:
        flash('สำหรับคณะกรรมการประเมิน PA เท่านั้น ขออภัยในความไม่สะดวก', 'warning')
        return redirect(url_for('pa.index'))
    return render_template('pa/eva_consensus_scoresheet.html', approved_scoresheets=approved_scoresheets)


@pa.route('/eva/consensus-scoresheets/<int:approved_id>', methods=['GET', 'POST'])
@login_required
def detail_consensus_scoresheet(approved_id):
    #TODO: recheck bug
    approve_scoresheet = PAApprovedScoreSheet.query.filter_by(id=approved_id).first()
    score_sheet_item = PAScoreSheetItem.query.filter_by(score_sheet_id=approve_scoresheet.score_sheet_id).all()
    if request.method == 'POST':
        approve_scoresheet.approved_at = datetime.datetime.now(tz)
        db.session.add(approve_scoresheet)
        db.session.commit()
        flash('บันทึกการอนุมัติเรียบร้อยแล้ว', 'success')
        return redirect(url_for('pa.consensus_scoresheets'))
    return render_template('pa/eva_consensus_scoresheet_detail.html', score_sheet_item=score_sheet_item,
                           approve_scoresheet=approve_scoresheet)

  
@pa.route('/eva/all-scoresheet')
@login_required
def all_scoresheet():
    committee = PACommittee.query.filter_by(staff=current_user).all()
    for c in committee:
        scoresheets = PAScoreSheet.query.filter_by(committee_id=c.id).all()
    if not committee:
        flash('สำหรับคณะกรรมการประเมิน PA เท่านั้น ขออภัยในความไม่สะดวก', 'warning')
        return redirect(url_for('pa.index'))
    return render_template('pa/eva_all_scoresheet.html', scoresheets=scoresheets)
