# from stockCore.models import KeyValueIndex, FilterCondition, UserFilterCondition, User, InterestRate, Stock
from stockCore.models import User,Stock ,StockRecord
import shioaji as sj # 載入永豐金Python API
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Avg ,Sum 
import csv
import os


def import_stocks():
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'stocks.csv')

    file = open(file_path)
    reader = csv.reader(file, delimiter=',')
    for index, row in enumerate(reader):
        if index != 0:
            if Stock.objects.filter(stock_code=row[0]).count()==0:
                stock = Stock()
            else:
                stock = Stock.objects.filter(stock_code=row[0]).first()
            
            stock.stock_code = row[0]
            stock.name = row[1]
            stock.stockIndustry = row[2]
            stock.stockFullName = row[3]
            stock.stockAddress = row[4]
            stock.stockChairman = row[5]
            stock.stockManager = row[6]
            stock.stockMainBusiness = row[7]
            stock.stockCreatedDate = row[8]
            stock.stockCapital = row[9]
            stock.stockIPODate = row[10]
            stock.stockState = row[11]
            stock.stockCommonSharePrice = row[12]
            stock.stockCommonShares = row[13]
            stock.stockDividendFrequency = row[14]
            stock.stockCompanyURL = row[15]
            stock.stockMoneyDJIntroduceURL = row[16]
            stock.save()

            print(stock.name + " " + stock.stock_code)

def import_stock_records():
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = "D122776936" #身分證字號
    PASSWORD = "Scott0815" #密碼
    api.login(PERSON_ID, PASSWORD) # 登入

    start_date = '2022-01-01'
    end_date = '20' + date.today().strftime("%y-%m-%d")
    stocks = Stock.objects.all()
    for stock in stocks:
        if (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=5))).count() == 0) and (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=2))).count() == 0):
            try:
                kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = start_date , end = end_date )
                df = pd.DataFrame({**kbars})
                df.ts = pd.to_datetime(df.ts)
                # df
                #分K轉成日K
                df.set_index(df.ts,inplace=True)
                df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume':'sum'})
                df.dropna(inplace=True)
                print(stock.stock_code)
                for index, row in df.iterrows():
                    try:
                        if StockRecord.objects.filter(stock=stock,date=row.name.date()).count()==0:
                            stockRecord = StockRecord()
                        else:
                            stockRecord = StockRecord.objects.filter(stock=stock,date=row.name.date()).first()
                        stockRecord.stock = stock
                        stockRecord.date = row.name.date()
                        stockRecord.OpeningPrice = round(Decimal(row.Open),2)
                        stockRecord.ClosingPrice = round(Decimal(row.Close),2)
                        stockRecord.DayHigh = round(Decimal(row.High),2)
                        stockRecord.DayLow = round(Decimal(row.Low),2)
                        stockRecord.Volume = round(Decimal(row.Volume),2)
                        stockRecord.save()
                    except:
                        # print(stock.stock_code + " Some data went wrong")
                        pass

            except:
                print(stock.name + " " + stock.stock_code  + " no index data.")

    api.logout() # 登出

def import_stock_records_MA():
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = "D122776936" #身分證字號
    PASSWORD = "Scott0815" #密碼
    api.login(PERSON_ID, PASSWORD) # 登入

    start_date = '2022-01-01'
    end_date = date.today().strftime("%Y-%m-%d")
    stocks = Stock.objects.all()
    for stock in stocks:
        # if (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=5))).count() == 0) and (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=2))).count() == 0):
            try:
                kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = start_date , end = end_date )
                df = pd.DataFrame({**kbars})
                df.ts = pd.to_datetime(df.ts)
                # df
                #分K轉成日K
                df.set_index(df.ts,inplace=True)
                df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume':'sum'})
                df.dropna(inplace=True)
                df['ma_s']=df.iloc[:,3].rolling(5).mean() 
                df['ma_m']=df.iloc[:,3].rolling(10).mean() 
                df['ma_l']=df.iloc[:,3].rolling(20).mean() 
                print(stock.stock_code)
                for index, row in df.iterrows():
                    try:
                        if StockRecord.objects.filter(stock=stock,date=row.name.date()).count()==0:
                            stockRecord = StockRecord()
                        else:
                            stockRecord = StockRecord.objects.filter(stock=stock,date=row.name.date()).first()
                        stockRecord.MA_5 = round(Decimal(row.ma_s),2)
                        stockRecord.MA_10 = round(Decimal(row.ma_m),2)
                        stockRecord.MA_20 = round(Decimal(row.ma_l),2)
     
                        stockRecord.save()
                    except:
                        # print(stock.stock_code + " Some data went wrong")
                        pass

            except:
                print(stock.name + " " + stock.stock_code  + " no index data.")

    api.logout() # 登出

