# -*- coding:utf-8 -*-
import textwrap
from main import db, ma
from sqlalchemy.sql import func


class Org(db.Model):
    __tablename__ = 'orgs'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False)
    en_name = db.Column('en_name', db.String())
    head = db.Column('head', db.String())
    parent_id = db.Column('parent_id', db.Integer, db.ForeignKey('orgs.id'))
    children = db.relationship('Org',
                               backref=db.backref('parent', remote_side=[id]))
    strategies = db.relationship('Strategy',
                                 backref=db.backref('org'))

    def __repr__(self):
        return self.name

    @property
    def active_staff(self):
        return [s for s in self.staff if s.retired is not True]


class Strategy(db.Model):
    __tablename__ = 'strategies'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    refno = db.Column('refno', db.String(), nullable=False)
    created_at = db.Column('created_at', db.DateTime(),
                           server_default=func.now())
    content = db.Column('content', db.String(), nullable=False)
    org_id = db.Column('org_id', db.Integer(),
                       db.ForeignKey('orgs.id'), nullable=False)
    tactics = db.relationship('StrategyTactic',
                              backref=db.backref('strategy'))


class StrategyTactic(db.Model):
    __tablename__ = 'strategy_tactics'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    refno = db.Column('refno', db.String(), nullable=False)
    created_at = db.Column('created_at', db.DateTime(), server_default=func.now())
    content = db.Column('content', db.String(), nullable=False)
    strategy_id = db.Column('strategy_id', db.Integer(),
                            db.ForeignKey('strategies.id'), nullable=False)
    themes = db.relationship('StrategyTheme',
                             backref=db.backref('tactic'))


class StrategyTheme(db.Model):
    __tablename__ = 'strategy_themes'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    refno = db.Column('refno', db.String(), nullable=False)
    created_at = db.Column('created_at', db.DateTime(), server_default=func.now())
    content = db.Column('content', db.String(), nullable=False)
    tactic_id = db.Column('tactic_id', db.Integer(),
                          db.ForeignKey('strategy_tactics.id'), nullable=False)
    activities = db.relationship('StrategyActivity',
                                 backref=db.backref('theme'))


class StrategyActivity(db.Model):
    __tablename__ = 'strategy_activities'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    refno = db.Column('refno', db.String(), nullable=False)
    created_at = db.Column('created_at', db.DateTime(), server_default=func.now())
    content = db.Column('content', db.String, nullable=False)
    theme_id = db.Column('theme_id', db.Integer(),
                         db.ForeignKey('strategy_themes.id'))
    kpis = db.relationship('KPI',
                           backref=db.backref('strategy_activity'))


class KPI(db.Model):
    __tablename__ = 'kpis'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    created_by = db.Column('created_by', db.String())
    created_at = db.Column('created_at', db.DateTime(), server_default=func.now())
    updated_at = db.Column('updated_at', db.DateTime(), onupdate=func.now())
    updated_by = db.Column('updated_by', db.String())
    name = db.Column('name', db.String, nullable=False, info={'label': u'ชื่อตัวชี้วัด'})
    refno = db.Column('refno', db.String(), info={'label': u'รหัสอ้างอิงตัวชี้วัด'})
    intent = db.Column('intent', db.String(), info={'label': u'จุดประสงค์'})
    frequency = db.Column('frequency', db.Integer(), info={'label': u'ความถี่'})
    unit = db.Column('unit', db.String(), info={'label': u'หน่วย'})
    source = db.Column('source', db.String(), info={'label': u'แหล่งข้อมูล'})
    available = db.Column('available', db.Boolean(), info={'label': u'พร้อมใช้'})
    availability = db.Column('availability', db.String(), info={'label': u'การเข้าถึงข้อมูล',
                                                                'choices': [(c, c) for c in [u'ไม่มีการรวบรวมข้อมูล',
                                                                                             u'ผ่านระบบอัตโนมัติทั้งหมด',
                                                                                             u'ต้องเตรียมข้อมูลเล็กน้อย',
                                                                                             u'ต้องเตรียมข้อมูลอย่างมาก']]})
    formula = db.Column('formula', db.String(), info={'label': u'สูตรคำนวณ'})
    keeper = db.Column('keeper', db.ForeignKey('staff_account.email'), info={'label': u'เก็บโดย'})
    note = db.Column('note', db.Text(), info={'label': u'หมายเหตุ'})
    target = db.Column('target', db.String(), info={'label': u'เป้าหมาย'})
    target_source = db.Column('target_source', db.String(), info={'label': u'ที่มาของการตั้งเป้าหมาย'})
    target_setter = db.Column('target_setter', db.String(), info={'label': u'ผู้ตั้งเป้าหมาย'})
    target_reporter = db.Column('target_reporter', db.String(), info={'label': u'ผู้รายงานเป้าหมาย'})
    target_account = db.Column('target_account', db.String(), info={'label': u'ผู้ดูแลเป้าหมาย'})
    reporter = db.Column('reporter', db.String(), info={'label': u'ผู้รายงาน'})
    consult = db.Column('consult', db.String(), info={'label': u'ที่ปรึกษา'})
    account = db.Column('account', db.String(), info={'label': u'ผู้รับผิดชอบ'})
    informed = db.Column('informed', db.String(), info={'label': u'ผู้รับรายงานหลัก'})
    pfm_account = db.Column('pfm_account', db.String(), info={'label': u'ผู้รับดูแลประสิทธิภาพตัวชี้วัด'})
    pfm_responsible = db.Column('pfm_resposible', db.String(), info={'label': u'ผู้รับผิดชอบประสิทธิภาพของตัวชี้วัด'})
    pfm_consult = db.Column('pfm_consult', db.String(), info={'label': u'ที่ปรึกษาประสิทธิภาพของตัวชี้วัด'})
    pfm_informed = db.Column('pfm_informed', db.String(), info={'label': u'ผู้รับรายงานเรื่องประสิทธิภาพตัวชี้วัดหลัก'})
    strategy_activity_id = db.Column('strategy_activity_id',
                                     db.ForeignKey('strategy_activities.id'))
    reportlink = db.Column('reportlink', db.String(), info={'label': u'หน้าแสดงผล (dashboard)'})


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column('id', db.String(), primary_key=True)
    refno = db.Column('refno', db.Integer(), nullable=False)
    title = db.Column('title', db.String())
    password = db.Column('password', db.String())
    th_first_name = db.Column('th_first_name', db.String(), nullable=False)
    th_last_name = db.Column('th_last_name', db.String(), nullable=False)
    en_first_name = db.Column('en_first_name', db.String())
    en_last_name = db.Column('en_last_name', db.String())

    def __str__(self):
        return u'ID:{} {} {}'.format(self.id, self.th_first_name, self.th_last_name)


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column('id', db.Integer(), primary_key=True)
    refno = db.Column('refno', db.String(), nullable=False)
    th_class_name = db.Column('th_class_name', db.String(), nullable=False)
    en_class_name = db.Column('en_class_name', db.String(), nullable=False)
    academic_year = db.Column('academic_year', db.String(4), nullable=False)
    deadlines = db.relationship('ClassCheckIn', backref=db.backref('class'))

    def __str__(self):
        return u'{} : {}'.format(self.refno, self.academic_year)


class ClassCheckIn(db.Model):
    __tablename__ = 'class_check_in'
    id = db.Column('id', db.Integer(), primary_key=True)
    class_id = db.Column('class_id', db.ForeignKey('classes.id'))
    deadline = db.Column('deadline', db.String())
    late_mins = db.Column('late_mins', db.Integer())
    class_ = db.relationship('Class', backref=db.backref('checkin_info'))

    def __str__(self):
        return self.class_.refno


class StudentCheckInRecord(db.Model):
    __tablename__ = 'student_check_in_records'
    id = db.Column('id', db.Integer(), primary_key=True)
    stud_id = db.Column('stud_id', db.ForeignKey('students.id'))
    student = db.relationship('Student', backref=db.backref('check_in_records'))
    classchk_id = db.Column('classchk_id', db.Integer(),
                            db.ForeignKey('class_check_in.id'), nullable=False)
    classchk = db.relationship('ClassCheckIn', backref=db.backref('student_records'))
    check_in_time = db.Column('checkin', db.DateTime(timezone=True), nullable=False)
    check_in_status = db.Column('status', db.String())
    elapsed_mins = db.Column('elapsed_mins', db.Integer())


class Province(db.Model):
    __tablename__ = 'provinces'
    id = db.Column('id', db.Integer(), primary_key=True)
    code = db.Column('code', db.String(), nullable=False)
    name = db.Column('name', db.String(40), nullable=False)
    districts = db.relationship("District",
                                backref=db.backref('parent'))


class District(db.Model):
    __tablename__ = 'districts'
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(40), nullable=False)
    code = db.Column('code', db.String(), nullable=False)
    province_id = db.Column(db.Integer(),
                            db.ForeignKey('provinces.id'))
    subdistricts = db.relationship('Subdistrict',
                                   backref=db.backref('district'))


class Subdistrict(db.Model):
    __tablename__ = 'subdistricts'
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(80), nullable=False)
    code = db.Column('code', db.String(), nullable=False)
    district_id = db.Column(db.Integer(),
                            db.ForeignKey('districts.id'))


class KPISchema(ma.ModelSchema):
    class Meta:
        model = KPI


class HomeAddress(db.Model):
    __tablename__ = 'addresses'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    village = db.Column(db.String(), nullable=True)
    street = db.Column(db.String(), nullable=True)
    province_id = db.Column('province_id', db.Integer(),
                            db.ForeignKey('provinces.id'))
    district_id = db.Column('district_id', db.Integer(),
                            db.ForeignKey('districts.id'))
    subdistrict_id = db.Column('subdistrict_id', db.Integer(),
                               db.ForeignKey('subdistricts.id'))
    postal_code = db.Column('postal_code', db.Integer())


class Mission(db.Model):
    __tablename__ = 'missions'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column('name', db.String(), nullable=False)

    def __repr__(self):
        return u'{}:{}'.format(self.id, self.name)

    def __str__(self):
        return u'{}'.format(self.name)


class CostCenter(db.Model):
    __tablename__ = 'cost_centers'
    id = db.Column('id', db.String(12), primary_key=True)

    def __repr__(self):
        return u'{}'.format(self.id)


class IOCode(db.Model):
    __tablename__ = 'iocodes'
    id = db.Column('id', db.String(16), primary_key=True)
    cost_center_id = db.Column('cost_center_id', db.String(),
                               db.ForeignKey('cost_centers.id'), nullable=False)
    cost_center = db.relationship('CostCenter', backref=db.backref('iocodes'))
    mission_id = db.Column('mission_id', db.Integer(), db.ForeignKey('missions.id'), nullable=False)
    mission = db.relationship('Mission', backref=db.backref('iocodes'))
    org_id = db.Column('org_id', db.Integer(), db.ForeignKey('orgs.id'), nullable=False)
    org = db.relationship('Org', backref=db.backref('iocodes'))
    name = db.Column('name', db.String(255), nullable=False)

    def __repr__(self):
        return u'{}:{}:{}:{}'.format(self.id, self.name, self.org.name, self.mission)

    def to_dict(self):
        return {
            'id': self.id,
            'costCenter': u'{}'.format(self.cost_center.id),
            'name': u'{}'.format(self.name),
            'org': u'{}'.format(self.org.name),
            'mission': u'{}'.format(self.mission.name)
        }


class OrgSchema(ma.ModelSchema):
    class Meta:
        model = Org


class Holidays(db.Model):
    __tablename__ = 'holidays'
    id = db.Column('id', db.Integer(), primary_key=True, autoincrement=True)
    holiday_date = db.Column('holiday_date', db.DateTime(timezone=True))
    holiday_name = db.Column('holiday_name', db.String())

    def tojson(self):
        return {"date": self.holiday_date, "name": self.holiday_name}


data_service_assoc = db.Table('data_service_assoc',
                              db.Column('data_id', db.Integer, db.ForeignKey('db_data.id'), primary_key=True),
                              db.Column('core_service_id', db.Integer, db.ForeignKey('db_core_services.id'),
                                        primary_key=True)
                              )

data_process_assoc = db.Table('data_process_assoc',
                              db.Column('data_id', db.Integer, db.ForeignKey('db_data.id'), primary_key=True),
                              db.Column('process_id', db.Integer, db.ForeignKey('db_processes.id'), primary_key=True),
                              )

dataset_service_assoc = db.Table('dataset_service_assoc',
                                 db.Column('dataset_id', db.Integer, db.ForeignKey('db_datasets.id'), primary_key=True),
                                 db.Column('core_service_id', db.Integer, db.ForeignKey('db_core_services.id'),
                                           primary_key=True)
                                 )

dataset_process_assoc = db.Table('dataset_process_assoc',
                                 db.Column('dataset_id', db.Integer, db.ForeignKey('db_datasets.id'), primary_key=True),
                                 db.Column('process_id', db.Integer, db.ForeignKey('db_processes.id'),
                                           primary_key=True),
                                 )

dataset_kpi_assoc = db.Table('dataset_kpi_assoc',
                             db.Column('dataset_id', db.Integer, db.ForeignKey('db_datasets.id'), primary_key=True),
                             db.Column('kpi_id', db.Integer, db.ForeignKey('kpis.id'), primary_key=True),
                             )

kpi_service_assoc = db.Table('kpi_service_assoc',
                             db.Column('kpi_id', db.Integer, db.ForeignKey('kpis.id'), primary_key=True),
                             db.Column('core_service_id', db.Integer, db.ForeignKey('db_core_services.id'),
                                       primary_key=True)
                             )

kpi_process_assoc = db.Table('kpi_process_assoc',
                             db.Column('kpi_id', db.Integer, db.ForeignKey('kpis.id'), primary_key=True),
                             db.Column('process_id', db.Integer, db.ForeignKey('db_processes.id'), primary_key=True)
                             )


pdpa_coordinators = db.Table('pdpa_coordinators',
                        db.Column('staff_id', db.Integer, db.ForeignKey('staff_account.id'), primary_key=True),
                        db.Column('db_core_service_id', db.Integer, db.ForeignKey('db_core_services.id'), primary_key=True)
                        )


from app.staff.models import StaffAccount


class CoreService(db.Model):
    __tablename__ = 'db_core_services'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    service = db.Column('service', db.String(255), nullable=False, info={'label': u'บริการ'})
    mission_id = db.Column('mission_id', db.ForeignKey('missions.id'))
    creator_id = db.Column('creator_id', db.ForeignKey('staff_account.id'))
    created_at = db.Column('created_at', db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column('updated_at', db.DateTime(timezone=True), onupdate=func.now())
    mission = db.relationship(Mission, backref=db.backref('services', lazy='dynamic',
                                                          cascade='all, delete-orphan'))
    data = db.relationship('Data', secondary=data_service_assoc, lazy='subquery',
                           backref=db.backref('core_services', lazy=True))
    kpis = db.relationship(KPI, secondary=kpi_service_assoc, lazy='subquery',
                           backref=db.backref('core_services', lazy=True))
    datasets = db.relationship('Dataset', secondary=dataset_service_assoc, lazy='subquery',
                               backref=db.backref('core_services', lazy=True))
    pdpa_coordinators = db.relationship(StaffAccount, secondary=pdpa_coordinators, lazy='subquery',
                           backref=db.backref('pdpa_services', lazy=True))

    def __str__(self):
        return u'{}'.format(self.service)


class Data(db.Model):
    __tablename__ = 'db_data'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    name = db.Column('name', db.String(255), nullable=False, info={'label': u'ข้อมูล'})
    created_at = db.Column('created_at', db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column('updated_at', db.DateTime(timezone=True), onupdate=func.now())
    creator_id = db.Column('creator_id', db.ForeignKey('staff_account.id'))


class Process(db.Model):
    __tablename__ = 'db_processes'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    category = db.Column('category', db.String(), nullable=False,
                         info={'label': u'กลุ่มงาน', 'choices': [(c, c) for c in ['back_office', 'regulation',
                                                                                  'performance', 'crm']]})
    name = db.Column('name', db.String(255), nullable=False, info={'label': u'กระบวนการ'})
    org_id = db.Column('org_id', db.ForeignKey('orgs.id'))
    org = db.relationship(Org, backref=db.backref('processes', lazy=True))
    created_at = db.Column('created_at', db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column('updated_at', db.DateTime(timezone=True), onupdate=func.now())
    creator_id = db.Column('creator_id', db.ForeignKey('staff_account.id'))
    data = db.relationship(Data, secondary=data_process_assoc, lazy='subquery',
                           backref=db.backref('processes', lazy=True))
    kpis = db.relationship(KPI, secondary=kpi_process_assoc, lazy='subquery',
                           backref=db.backref('processes', lazy=True))
    datasets = db.relationship('Dataset', secondary=dataset_process_assoc, lazy='subquery',
                               backref=db.backref('processes', lazy=True))


class Dataset(db.Model):
    __tablename__ = 'db_datasets'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    reference = db.Column('reference', db.String(255),
                          nullable=False, info={'label': u'รหัสข้อมูล'})
    name = db.Column('name', db.String(255), info={'label': u'ชื่อ'})
    desc = db.Column('desc', db.Text(), info={'label': u'รายละเอียด'})
    source_url = db.Column('source_url', db.Text(), info={'label': u'URL แหล่งข้อมูล'})
    data_id = db.Column('data_id', db.ForeignKey('db_data.id'))
    created_at = db.Column('created_at', db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column('updated_at', db.DateTime(timezone=True), onupdate=func.now())
    creator_id = db.Column('creator_id', db.ForeignKey('staff_account.id'))
    maintainer_id = db.Column('maintainer_id', db.ForeignKey('staff_account.id'))
    sensitive = db.Column('sensitive', db.Boolean(), default=False, info={'label': u'ข้อมูลอ่อนไหว'})
    personal = db.Column('personal', db.Boolean(), default=False, info={'label': u'ข้อมูลส่วนบุคคล'})
    data = db.relationship(Data, backref=db.backref('datasets', lazy='dynamic', cascade='all, delete-orphan'))
    kpis = db.relationship(KPI, secondary=dataset_kpi_assoc, lazy='subquery',
                           backref=db.backref('datasets', lazy=True))


ropa_subject_assoc = db.Table('ropa_service_assoc',
                              db.Column('ropa_id', db.Integer, db.ForeignKey('db_ropas.id'), primary_key=True),
                              db.Column('subject_id', db.Integer, db.ForeignKey('db_data_subjects.id'),
                                        primary_key=True))


class DataSubject(db.Model):
    __tablename__ = 'db_data_subjects'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    subject = db.Column('subject', db.String(), nullable=False, info={'label': u'เจ้าของข้อมูล'})


class DataStorage(db.Model):
    __tablename__ = 'db_storages'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    type_ = db.Column('type', db.String(), nullable=False, info={'label': u'ประเภท',
                                                                 'choices': [(c, c) for c in
                                                                             [u'ฐานข้อมูล',
                                                                              u'Excel',
                                                                              'Google sheet',
                                                                              u'กระดาษ',
                                                                              u'อื่น ๆ']]})
    desc = db.Column('desc', db.String(), info={'label': u'รายละเอียด'})



class ROPA(db.Model):
    __tablename__ = 'db_ropas'
    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    dataset_id = db.Column('dataset_id', db.ForeignKey('db_datasets.id'))
    dataset = db.relationship(Dataset, backref=db.backref('ropa', uselist=False))
    major_objective = db.Column('major_objective', db.Text(), info={'label': u'จุดประสงค์หลักในการเก็บข้อมูล'})
    minor_objective = db.Column('minor_objective', db.Text(), info={'label': u'จุดประสงค์รองในการเก็บข้อมูล'})
    subjects = db.relationship(DataSubject,
                               secondary=ropa_subject_assoc,
                               lazy='subquery',
                               backref=db.backref('subjects', lazy=True))
    personal_data = db.Column('personal_data', db.String(), info={'label': u'ประเภทข้อมูลส่วนบุคคล'})
    personal_data_desc = db.Column('personal_data_desc', db.Text(), info={'label': u'รายละเอียดข้อมูลส่วนบุคคล'})
    sensitive_data = db.Column('sensitive_data', db.Text(), info={'label': u'ข้อมูลอ่อนไหว'})
    consent_required = db.Column('consent_required', db.Boolean(), default=False, info={'label': u'ต้องการ consent'})
    amount = db.Column('amount', db.String(), info={'label': u'ปริมาณข้อมูล'})
    is_primary_data = db.Column('is_primary_data', db.Boolean(), info={'label': u'เก็บข้อมูลจากเจ้าของโดยตรงหรือไม่'})
    law_basis = db.Column('law_basis', db.Text(), info={'label': u'แหล่งที่มาของข้อมูล',
                                                        'choices': [(c, c) for c in
                                                                    [u'ฐานจัดทำหมายเหตุ/วิจัย/สถิติ',
                                                                     u'ฐานป้องกันหรือระงับอันตรายต่อชีวิต',
                                                                     u'ฐานปฏิบัติตามสัญญา',
                                                                     u'ฐานประโยชน์สาธารณะ',
                                                                     u'ฐานประโยชน์โดยชอบด้วยกฎหมาย',
                                                                     u'ฐานการปฏิบัติตามกฎหมาย',
                                                                     u'ฐานความยินยอม']]})
    source = db.Column('source', db.Text(), info={'label': u'แหล่งที่มาของข้อมูล'})
    format = db.Column('format', db.Text(), info={'label': u'รูปแบบการเก็บข้อมูล'})
    storage = db.Column('storage', db.Text(), info={'label': u'สถานที่เก็บข้อมูล'})
    duration = db.Column('duration', db.Text(), info={'label': u'ระยะเวลาในการเก็บข้อมูล'})
    destroy_method = db.Column('destroy_method', db.Text(), info={'label': u'การทำลายข้อมูลหลังหมดอายุ'})
    inside_sharing = db.Column('inside_sharing', db.Text(), info={'label': u'การแลกเปลี่ยนข้อมูลในหน่วยงาน'})
    outside_sharing = db.Column('outside_sharing', db.Text(), info={'label': u'การแลกเปลี่ยนข้อมูลนอกหน่วยงาน'})
    intl_sharing = db.Column('intl_sharing', db.Text(), info={'label': u'มาตรการในการแลกเปลี่ยนข้อมูลต่างประเทศ'})
    security_measure = db.Column('security_measure', db.Text(),
                                 info={'label': u'มาตรการควบคุมข้อมูลส่วนบุคคลในปัจจุบัน'})
    updated_at = db.Column('updated_at', db.DateTime(timezone=True), onupdate=func.now())
    updater_id = db.Column('updater_id', db.ForeignKey('staff_account.id'))
    updater = db.relationship(StaffAccount)
