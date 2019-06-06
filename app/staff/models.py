from ..main import db


class StaffAccount(db.Model):
    __tablename__ = 'staff_account'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    personal_id = db.Column('personal_id', db.ForeignKey('staff_personal_info.id'))
    email = db.Column('email', db.String(), unique=True)
    personal_info = db.relationship("StaffPersonalInfo", backref=db.backref("staff_account", uselist=False))
    password = db.Column('password', db.String(255), nullable=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __str__(self):
        return u'{}'.format(self.email)


class StaffPersonalInfo(db.Model):
    __tablename__ = 'staff_personal_info'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    en_firstname = db.Column('en_firstname', db.String(), nullable=False)
    en_lastname = db.Column('en_lastname', db.String(), nullable=False)
    highest_degree_id = db.Column('highest_degree_id', db.ForeignKey('staff_edu_degree.id'))
    highest_degree = db.relationship('StaffEduDegree',
                        backref=db.backref('staff_personal_info', uselist=False))
    th_firstname = db.Column('th_firstname', db.String(), nullable=False)
    th_lastname = db.Column('th_lastname', db.String(), nullable=False)
    academic_position_id = db.Column('academic_position_id', db.ForeignKey('staff_academic_position.id'))
    academic_position = db.relationship('StaffAcademicPosition', backref=db.backref('staff_list'))
    orgs_id = db.Column('orgs_id', db.ForeignKey('orgs.id'))

    def __str__(self):
        return u'{} {}'.format(self.en_firstname, self.en_lastname)


class StaffEduDegree(db.Model):
    __tablename__ = 'staff_edu_degree'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    level = db.Column('level', db.String(), nullable=False)
    en_title = db.Column('en_title', db.String())
    th_title = db.Column('th_title', db.String())
    en_major = db.Column('en_major', db.String())
    th_major = db.Column('th_major', db.String())
    en_school = db.Column('en_school', db.String())
    th_country = db.Column('th_country', db.String())


class StaffAcademicPosition(db.Model):
    __tablename__ = 'staff_academic_position'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    position_full_th = db.Column('position_full_th', db.String(), nullable=False)
    position_abbr_th = db.Column('position_abbr_th', db.String(), nullable=False)
    position_full_en = db.Column('position_full_en', db.String(), nullable=False)
    position_abbr_en = db.Column('position_abbr_en', db.String(), nullable=False)
    level = db.Column('level', db.Integer(), nullable=False)
