import os
from celery import Celery
from celery.schedules import crontab
from datetime import date, datetime, timedelta, timezone
import shioaji as sj  # 載入永豐金Python API
import pandas as pd
from decimal import Decimal
from requests.auth import HTTPProxyAuth
import decimal
from django.db.models import Avg, Sum

# from __future__ import absolute_import
# from celery import Celery
# app = Celery('test_celery',
#           broker='amqp://maxat:password123@localhost/maxat_vhost',
#           backend='rpc://',
#           include=['test_celery.tasks'])

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
app = Celery('celery')


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# response = app.control.enable_events(reply=True)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    # sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    # sender.add_periodic_task(60.0, send_user_notify_price_message.s('world'), expires=10)

    # server use UTC time, it should be Taiwan time -8 hour, ex 10:00am taipei task, should set 02:00am server task
    # Daily task
    # sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # run at 1500 every Taiwan time
    # sender.add_periodic_task(
    #     30.0, test.s('test'), name='add every 10')

    # sender.add_periodic_task(
    #     crontab(hour=8, minute=40, day_of_week='1-5'),
    #     get_stock_datas.s('crawl today stock record'),
    # )

    # sender.add_periodic_task(
    #     crontab(hour=5, minute=18),
    #     get_stock_day_recommend.s('get today stock recommend'),
    # )

    # sender.add_periodic_task(
    #     crontab(hour=5, minute=24),
    #     get_recent_N_font_stock.s('get recent N font type stock'),
    # )

    sender.add_periodic_task(
        crontab(hour=3, minute=40),
        import_stock_records.s('import_stock_records'),
    )


@app.task
def test(arg):
    from stockCrawler.tasks.tasks import test
    test(arg)


@app.task
def get_stock_datas(arg):
    from stockCrawler.tasks.tasks import get_stock_datas
    get_stock_datas(arg)


@app.task
def get_stock_day_recommend(args):
    from stockCrawler.tasks.tasks import get_stock_day_recommend
    get_stock_day_recommend(args)


@app.task
def get_recent_N_font_stock(args):
    from stockCrawler.tasks.tasks import get_recent_N_font_stock
    get_recent_N_font_stock(args)


@app.task
def import_stock_records(args):
    from stockCrawler.tasks.tasks_seed import import_stock_records
    import_stock_records(args)
