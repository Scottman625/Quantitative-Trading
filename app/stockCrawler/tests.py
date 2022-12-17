from django.test import TestCase
from datetime import date, datetime, timedelta ,timezone

a = datetime.utcnow().replace(tzinfo=timezone.utc).weekday()
print(a)
# Create your tests here.
