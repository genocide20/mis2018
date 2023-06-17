from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, widgets
from wtforms.validators import DataRequired
from wtforms_alchemy import model_form_factory, QuerySelectField, QuerySelectMultipleField

from app.PA.models import *
from app.main import db

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class PAKPIItemForm(ModelForm):
    class Meta:
        model = PAKPIItem

    level = QuerySelectField(query_factory=lambda: PALevel.query.all(),
                           get_label='level',
                           label=u'เกณฑ์การประเมิน',
                           blank_text='กรุณาเลือกเกณฑ์การประเมิน..', allow_blank=True)


class PAKPIForm(ModelForm):
    class Meta:
        model = PAKPI
    pa_kpi_items = FieldList(FormField(PAKPIItemForm, default=PAKPIItem), min_entries=5)


class PAItemForm(ModelForm):
    class Meta:
        model = PAItem

    items = FieldList(FormField(PAKPIForm, default=PAKPI), min_entries=1)
    kpis = QuerySelectMultipleField('ตัวชี้วัดเป้าหมายความสำเร็จของภาระงาน',
                                    query_factory=lambda: PAKPI.query.all(),
                                    widget=widgets.ListWidget(prefix_label=False),
                                    option_widget=widgets.CheckboxInput())





