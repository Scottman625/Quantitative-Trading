from django.test import TestCase
from datetime import date, datetime, timedelta, timezone
import pytz
import pandas as pd

list_x = ['a', 'b', 'c']


dict = {}

for item in list_x:
    dict[item] = 3

print(dict)
