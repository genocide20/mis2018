from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, IntegerField, HiddenField, FloatField
from wtforms.validators import DataRequired, optional


class ServiceForm(FlaskForm):
    location = StringField('Location', validators=[DataRequired()])
    service_date = DateField('Service Date', validators=[DataRequired()])


class TestProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Description', validators=[DataRequired()])
    age_max = IntegerField('Age max', validators=[optional()])
    age_min = IntegerField('Age min', validators=[optional()])
    gender = SelectField('Gender', choices=[(0, 'Female'),
                                            (1, 'Male'),
                                            (2, 'All')],
                         default=2, coerce=int)
    quote = FloatField('Quote', validators=[optional()])


class TestGroupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Description', validators=[DataRequired()])
    age_max = IntegerField('Age max', validators=[optional()])
    age_min = IntegerField('Age min', validators=[optional()])
    gender = SelectField('Gender', choices=[(0, 'Female'),
                                            (1, 'Male'),
                                            (2, 'All')],
                         default=2, coerce=int)


class TestListForm(FlaskForm):
    set_id = HiddenField('Set ID', validators=[DataRequired()])
    test_list = HiddenField('Test List', validators=[DataRequired()])


class TestForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    desc = StringField('Description', validators=[DataRequired()])
    default_price = FloatField('Default Price', validators=[optional()])
    container = SelectField('Container', coerce=int)


class CustomerForm(FlaskForm):
    org_id = HiddenField('org_id')
    service_id = HiddenField('service_id')
    title = StringField('Title')
    firstname = StringField('First Name')
    lastname = StringField('Last Name')
    dob = StringField('Date of Birth', validators=[optional()])
    age = IntegerField('Age', validators=[optional()])
    gender = SelectField('Gender', choices=[(0, 'Female'), (1, 'Male')],
                         coerce=int, default=0)
    phone = StringField('Phone', validators=[optional()])
    emptype = SelectField('Employment Type', validators=[DataRequired()], coerce=int)
    emp_id  = StringField('Employee ID', validators=[optional()])
    dept = StringField('Deparment', validators=[optional()])
    division = StringField('Division', validators=[optional()])
    unit = StringField('Unit', validators=[optional()])