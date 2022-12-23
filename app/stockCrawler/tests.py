from django.test import TestCase
from datetime import date, datetime, timedelta ,timezone
import pytz
tw = pytz.timezone('Asia/Taipei')
twdt = tw.localize(datetime.now())
a = twdt.date()
print(a)
# Create your tests here.
