# from .models import Stock, StockRecord, User
from .models import Stock, StockRecord, User
import shioaji as sj # 載入永豐金Python API
import pandas as pd
from datetime import date, timedelta
# from stockCore.models import User,Stock ,StockRecord

sj.__version__ # 版本為 "0.3.6.dev3"
api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
PERSON_ID = "D122776936" #身分證字號
PASSWORD = "Scott0815" #密碼
api.login(PERSON_ID, PASSWORD) # 登入

stock = Stock.objects.get(stock_code='6689')
start_date = '2022-01-01'
end_date = '20' + date.today().strftime("%y-%m-%d")
kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = start_date , end = end_date )
df = pd.DataFrame({**kbars})
df.ts = pd.to_datetime(df.ts)
# df
#分K轉成日K
df.set_index(df.ts,inplace=True)
df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume':'sum'})
df.dropna(inplace=True)
for index, row in df.iterrows():

    if StockRecord.objects.filter(stock=stock,date=row.name.date()).count()==0:
        stockRecord = StockRecord()
    else:
        stockRecord = StockRecord.objects.filter(stock=stock,date=row.name.date()).first()

    stockRecord.stock = stock
    stockRecord.date = row.name.date()
    stockRecord.OpeningPrice = row.Open
    stockRecord.ClosingPrice = row.Close
    stockRecord.DayHigh = row.High
    stockRecord.DayLow = row.Close
    stockRecord.Volume = row.Volume
    stockRecord.save()