from django.test import TestCase
from datetime import date, datetime, timedelta ,timezone
import pytz
# tw = pytz.timezone('Asia/Taipei')
# twdt = tw.localize(datetime.now())
# a = twdt.date()
# print((datetime.strptime("2022-12-26","%Y-%m-%d").date() - timedelta(days=2)).strftime("%Y-%m-%d"))
# Create your tests here.
results = [[]] * 5
def function():
    return [lambda x:i * x for i in range(5)]

for i in range(5):
    for j, f in enumerate(function()):
        results[j].append(f(i))
print(results)