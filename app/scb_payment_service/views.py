import datetime
import os

import requests
from flask import jsonify, request, render_template
from flask_jwt_extended import (create_access_token, get_jwt_identity, jwt_required, get_current_user,
                                create_refresh_token)
from werkzeug.security import check_password_hash

from . import scb_payment
from .models import ScbPaymentServiceApiClientAccount, ScbPaymentRecord
from ..main import csrf, db
import uuid

AUTH_URL = os.environ.get('SCB_AUTH_URL')
QRCODE_URL = os.environ.get('SCB_QRCODE_URL')
APP_KEY = os.environ.get('SCB_APP_KEY')
APP_SECRET = os.environ.get('SCB_APP_SECRET')
BILLERID = os.environ.get('BILLERID')
REF3 = os.environ.get('SCB_REF3')
QR30_INQUIRY = os.environ.get('QR30_INQUIRY')
SLIP_VERIFICATION = os.environ.get('SLIP_VERIFICATION')


def generate_qrcode(amount, ref1, ref2, ref3):
    headers = {
        'Content-Type': 'application/json',
        'requestUId': str(uuid.uuid4()),
        'resourceOwnerId': APP_KEY
    }
    response = requests.post(AUTH_URL, headers=headers, json={
        'applicationKey': APP_KEY,
        'applicationSecret': APP_SECRET
    })
    response_data = response.json()
    print(response.text)
    access_token = response_data['data']['accessToken']

    headers['authorization'] = 'Bearer {}'.format(access_token)

    qrcode_resp = requests.post(QRCODE_URL, headers=headers, json={
        'qrType': 'PP',
        'amount': '{}'.format(amount),
        'ppType': 'BILLERID',
        'ppId': BILLERID,
        'ref1': ref1,
        'ref2': ref2,
        'ref3': ref3,
        'expiryDate': '2023-11-30 23:35:33',
        'numberOfTimes': 1
    })
    if qrcode_resp.status_code == 200:
        qr_image = qrcode_resp.json()['data']['qrImage']
        return {'qrImage': qr_image}
    else:
        return qrcode_resp.json()


@scb_payment.route('/api/v1.0/login', methods=['POST'])
@csrf.exempt
def login():
    client_id = request.get_json().get('client_id')
    client_secret = request.get_json().get('client_secret')
    client = ScbPaymentServiceApiClientAccount.query.get(client_id)
    if client:
        if check_password_hash(client._secret_hash, client_secret):
            return jsonify(access_token=create_access_token(identity=client_id),
                           refresh_token=create_refresh_token(identity=client_id))
        else:
            return jsonify({'message': 'Invalid client secret.'}), 403
    else:
        return jsonify({'message': 'Client account not found.'}), 404


@scb_payment.route('/api/v1.0/refresh', methods=['POST'])
@jwt_required(refresh=True)
@csrf.exempt
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200


@scb_payment.route('/api/v1.0/qrcode/create', methods=['POST'])
@jwt_required()
@csrf.exempt
def create_qrcode():
    # TODO: set expiration time to 60 minutes.
    amount = request.get_json().get('amount')
    ref1 = request.get_json().get('ref1')
    ref2 = request.get_json().get('ref2')
    customer1 = request.get_json().get('customer1')
    customer2 = request.get_json().get('customer2')
    service = request.get_json().get('service')
    record = ScbPaymentRecord.query.filter_by(bill_payment_ref1=ref1, bill_payment_ref2=ref2).first()
    if amount is None:
        return jsonify({'message': 'Amount is needed'}), 400
    data = generate_qrcode(amount, ref1=ref1, ref2=ref2, ref3=REF3)
    if 'qrImage' not in data:
        if not record:
            record = ScbPaymentRecord(bill_payment_ref1=ref1, bill_payment_ref2=ref2,
                                      service=service,
                                      customer1=customer1, customer2=customer2,
                                      amount=amount)
            db.session.add(record)
            db.session.commit()
        return jsonify({'data': data})
    else:
        return jsonify(data), 500


@scb_payment.route('/api/v1.0/payment-confirm', methods=['GET', 'POST'])
@csrf.exempt
def confirm_payment():
    data = request.get_json()
    record = ScbPaymentRecord.query.filter_by(bill_payment_ref1=data['billPaymentRef1'],
                                              bill_payment_ref2=data['billPaymentRef2']).first()
    record.assign_data_from_request(data)
    db.session.add(record)
    db.session.commit()
    print(data)
    return jsonify({
        'resCode': '00',
        'recDesc': 'success',
        'transactionId': data['transactionId']
    })


@scb_payment.route('/api/v1.0/test-login')
@jwt_required()  # jwt_required has changed to jwt_required() in >=4.0
def test_login():
    current_user = get_current_user()  # return an account object from the user_loader_callback_loader
    return jsonify(logged_in_as=current_user.account_id), 200


@scb_payment.route('/verify-slip')
def verify_slip():
    transaction_id = request.args.get('transaction_id')
    print(transaction_id)
    if transaction_id:
        trnx = ScbPaymentRecord.query.filter_by(transaction_id=transaction_id).first()
        headers = {
            'Content-Type': 'application/json',
            'requestUId': str(uuid.uuid4()),
            'resourceOwnerId': APP_KEY
        }
        response = requests.post(AUTH_URL, headers=headers, json={
            'applicationKey': APP_KEY,
            'applicationSecret': APP_SECRET
        })
        response_data = response.json()
        access_token = response_data['data']['accessToken']

        headers['authorization'] = 'Bearer {}'.format(access_token)
        resp = requests.get(
            "{}/{}?sendingBank={}".format(SLIP_VERIFICATION, trnx.transaction_id, trnx.sending_bank_code),
            headers=headers)
        return jsonify(resp.json())
    records = ScbPaymentRecord.query.all()
    return render_template('scb_payment_service/verify_slips.html', records=records)


@scb_payment.route('/transaction-inquiry')
def transaction_inquiry():
    bill_payment_ref1 = request.args.get('bill_payment_ref1')
    bill_payment_ref2 = request.args.get('bill_payment_ref2')
    print(bill_payment_ref1)
    trnx = None
    if bill_payment_ref1 and bill_payment_ref2:
        trnx = ScbPaymentRecord.query.filter_by(bill_payment_ref1=bill_payment_ref1,
                                                bill_payment_ref2=bill_payment_ref2).first()
    elif bill_payment_ref1:
        trnx = ScbPaymentRecord.query.filter_by(bill_payment_ref1=bill_payment_ref1).first()

    if trnx:
        headers = {
            'Content-Type': 'application/json',
            'requestUId': str(uuid.uuid4()),
            'resourceOwnerId': APP_KEY
        }
        response = requests.post(AUTH_URL, headers=headers, json={
            'applicationKey': APP_KEY,
            'applicationSecret': APP_SECRET
        })
        response_data = response.json()
        access_token = response_data['data']['accessToken']

        headers['authorization'] = 'Bearer {}'.format(access_token)
        resp = requests.get(
            QR30_INQUIRY,
            params={"billerId": BILLERID,
                    "reference1": trnx.bill_payment_ref1,
                    "transactionDate": trnx.created_datetime.strftime("%Y-%m-%d"),
                    "eventCode": "00300100"}
            , headers=headers)
        return jsonify(resp.json())
    records = ScbPaymentRecord.query.all()
    return render_template('scb_payment_service/transaction_inquiry.html', records=records)


@scb_payment.route('/api/v1.0/check-payment')
@jwt_required()
def check_payment():
    bill_payment_ref1 = request.args.get('bill_payment_ref1')
    bill_payment_ref2 = request.args.get('bill_payment_ref2')
    if bill_payment_ref1 and bill_payment_ref2:
        trnx = ScbPaymentRecord.query.filter_by(bill_payment_ref1=bill_payment_ref1,
                                                bill_payment_ref2=bill_payment_ref2).first()
        if trnx:
            if trnx.payer_name is None and trnx.payer_account_number is None and trnx.sending_bank_code is None:
                headers = {
                    'Content-Type': 'application/json',
                    'requestUId': str(uuid.uuid4()),
                    'resourceOwnerId': APP_KEY
                }
                response = requests.post(AUTH_URL, headers=headers, json={
                    'applicationKey': APP_KEY,
                    'applicationSecret': APP_SECRET
                })
                response_data = response.json()
                access_token = response_data['data']['accessToken']

                headers['authorization'] = 'Bearer {}'.format(access_token)
                resp = requests.get(
                    QR30_INQUIRY,
                    params={"billerId": BILLERID,
                            "reference1": trnx.bill_payment_ref1,
                            "transactionDate": trnx.created_datetime.strftime("%Y-%m-%d"),
                            "eventCode": "00300100"}
                    , headers=headers)
                data = resp.json().get('data')
                if data:
                    trnx.payer_name = data.get('sender', {}).get('name')
                    trnx.payer_account_number = data.get('sender', {}).get('account', {}).get('value')
                    trnx.sending_bank_code = data.get('sendingBank')
                    trans_date_time = data.get('transDate') + ' ' + data.get('transTime')
                    trans_date_time = datetime.strptime(trans_date_time, '%Y%m%d %H:%M:%S')
                    trnx.transaction_dateand_time = trans_date_time
                    db.session.add(data)
                    db.session.commit()
            return jsonify({'data': {
                'payer_name': trnx.payer_name,
                'payer_account_number': trnx.payer_account_number,
                'sending_bank_code': trnx.sending_bank_code,
                'transaction_dateand_time': trnx.transaction_dateand_time,
                'bill_payment_ref1': trnx.bill_payment_ref1,
                'bill_payment_ref2': trnx.bill_payment_ref2,
                'transaction_id': trnx.transaction_id,
                'amount': trnx.amount
            }})
