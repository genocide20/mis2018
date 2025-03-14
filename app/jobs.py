import os
import requests
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig()


def send_event_notification():
    events = requests.get('https://mumtmis.herokuapp.com/linebot/events/notification')


scheduler = BlockingScheduler()
scheduler.add_job(send_event_notification,
                  'cron', day_of_week='mon-fri',
                  hour='7',
                  minute='30',
                  timezone='Asia/Bangkok')
scheduler.start()
