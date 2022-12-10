import shioaji as sj # 載入永豐金Python API
import pandas as pd
from datetime import date, timedelta
for x in range(5):
    for i in range(10):
        c = x*i
        if i == 5:
            continue
print(type(date.today() - timedelta(days=(5))))