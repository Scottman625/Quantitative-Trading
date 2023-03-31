from django.test import TestCase
from datetime import date, datetime, timedelta ,timezone
import pytz
import pandas as pd

item_colums = []
columns = []
list = [1,3,4,5]
for x in range(19,-1,-1):
    item_colums.append(list)


# for x in range(19,-1,-1):
#     item_colums.append(x)
print(item_colums)
# df = pd.DataFrame (item_colums, columns = ['x' ,'x+1'])
# print (df)

row=len(item_colums)
column=len(item_colums[0])
print(item_colums[0])
print(f'Rows:{row}, Column:{column}')
print("Shape of a list:",len(item_colums))