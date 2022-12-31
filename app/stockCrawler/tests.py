from django.test import TestCase
from datetime import date, datetime, timedelta ,timezone
import pytz
# tw = pytz.timezone('Asia/Taipei')
# twdt = tw.localize(datetime.now())
# a = twdt.date()
# print((datetime.strptime("2022-12-26","%Y-%m-%d").date() - timedelta(days=2)).strftime("%Y-%m-%d"))
# Create your tests here.
a = None
for i in range(0):
    if i > 11:
        a = i
if a == None:
    print('test')