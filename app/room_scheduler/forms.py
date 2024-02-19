from datetime import datetime

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import Field
from wtforms.widgets import TextInput
from wtforms_alchemy import (model_form_factory, QuerySelectField, QuerySelectMultipleField)
from app.room_scheduler.models import *
from app.staff.models import StaffAccount, StaffGroupDetail

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class DateTimePickerField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return self.data.strftime('%d-%m-%Y %H:%M:%S')
        else:
            return ''

    def process_formdata(self, value):
        if value[0]:
            self.data = datetime.strptime(value[0], '%d-%m-%Y %H:%M:%S')
        else:
            self.data = None


def get_own_and_public_groups():
    public_groups = set(StaffGroupDetail.query.filter_by(public=True))
    own_groups = set([team.group_detail for team in current_user.teams])
    return public_groups.union(own_groups)


class RoomEventForm(ModelForm):
    class Meta:
        model = RoomEvent

    start = DateTimePickerField('เริ่มต้น')
    end = DateTimePickerField('สิ้นสุด')

    category = QuerySelectField(query_factory=lambda: EventCategory.query.all())
    participants = QuerySelectMultipleField(query_factory=lambda: StaffAccount.get_active_accounts(),
                                            get_label='fullname')
    groups = QuerySelectMultipleField('กลุ่ม', query_factory=get_own_and_public_groups, get_label='activity_name')