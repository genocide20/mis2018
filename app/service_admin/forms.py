from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms_alchemy import model_form_factory, QuerySelectField
from app.academic_services.models import *
from flask_login import current_user
from sqlalchemy import or_

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class ServiceCustomerInfoForm(ModelForm):
    class Meta:
        model = ServiceCustomerInfo

    type = QuerySelectField('ประเภท', query_factory=lambda: ServiceCustomerType.query.all(), allow_blank=True,
                                blank_text='กรุณาเลือกประเภท', get_label='type')


class ServiceCustomerAddressForm(ModelForm):
    class Meta:
        model = ServiceCustomerAddress


def formatted_request_data():
    admin = ServiceAdmin.query.filter_by(admin_id=current_user.id).all()
    labs = []
    sub_labs = []
    for a in admin:
        if a.lab:
            labs.append(a.lab.code)
        else:
            sub_labs.append(a.sub_lab.code)
    query = ServiceRequest.query.filter(or_(ServiceRequest.admin.has(id=current_user.id), ServiceRequest.lab.in_(labs))) \
        if labs else ServiceRequest.query.filter(
        or_(ServiceRequest.admin.has(id=current_user.id), ServiceRequest.lab.in_(sub_labs)))
    return query


class ServiceResultForm(ModelForm):
    class Meta:
        model = ServiceResult

    file_upload = FileField('File Upload')
    request = QuerySelectField('เลขใบคำร้องขอ', query_factory=lambda: formatted_request_data(), allow_blank=True,
                               blank_text='กรุณาเลือกเลขใบคำร้องขอ')