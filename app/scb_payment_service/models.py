import secrets
import string
from sqlalchemy import func
from werkzeug import generate_password_hash, check_password_hash

from app.main import db

alphabet = string.digits + string.ascii_letters


class ApiClientAccount(db.Model):
    __tablename__ = 'api_client_accounts'
    _account_id = db.Column('account_id', db.String(), nullable=False, primary_key=True)
    _secret_hash = db.Column('secret_hash', db.String(), nullable=False)
    is_active = db.Column('is_active', db.Boolean(), default=True)
    created_at = db.Column('created_at', db.DateTime(timezone=True),
                           server_default=func.utcnow())
    updated_at = db.Column('updated_at', db.DateTime(timezone=True),
                           onupdate=func.utcnow())

    @property
    def account_id(self):
        return self._account_id

    @account_id.setter
    def set_account_id(self):
        self._account_id = ''.join(secrets.choice(string.digits) for i in range(8))

    @property
    def secret(self):
        raise ValueError('Client secret is not accessible.')

    @secret.setter
    def set_secret(self):
        secret = ''.join(secrets.choice(alphabet) for i in range(16))
        self._secret_hash = generate_password_hash(secret)
        print('The client secret is {}. Please keep it safe.'.format(secret))
