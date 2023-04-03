# from stockCore.models import KeyValueIndex, FilterCondition, UserFilterCondition, User, InterestRate, Stock
from stockCore.models import User, Stock, StockRecord
import shioaji as sj  # 載入永豐金Python API
import pandas as pd
from datetime import date, datetime, timedelta, timezone
import pytz
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Avg, Sum
import csv
import os
import decimal
from django.db.models import Avg, Sum


def import_stocks():
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'stocks.csv')

    file = open(file_path)
    reader = csv.reader(file, delimiter=',')
    for index, row in enumerate(reader):
        if index != 0:
            if Stock.objects.filter(stock_code=row[0]).count() == 0:
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


def import_stock_records(args):
    from stockCore.models import User, Stock, StockRecord
    user = User.objects.get(id=1)
    print(user)
    sj.__version__  # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False)  # simulation=False 即表示使用正式環境
    api.login(user.API_Key, user.Secret_Key)  # 登入

    tw = pytz.timezone('Asia/Taipei')
    twdt = tw.localize(datetime.now())
    weekday = twdt.weekday()
    if twdt.hour < 13:
        weekday = weekday - 1
    if weekday == 5:
        start_date = (twdt.date() - timedelta(days=1)).strftime("%Y-%m-%d")

    elif weekday == 6:
        start_date = (twdt.date() - timedelta(days=2)).strftime("%Y-%m-%d")
    elif weekday == -1:
        start_date = (twdt.date() - timedelta(days=3)).strftime("%Y-%m-%d")
    else:
        start_date = twdt.date().strftime("%Y-%m-%d")

    start_date = '2016-01-01'
    end_date = '2022-07-01'
    if weekday == 0:
        EMA_start_date = datetime.strptime(
            start_date, "%Y-%m-%d").date() - timedelta(days=3)
    else:
        EMA_start_date = datetime.strptime(
            start_date, "%Y-%m-%d").date() - timedelta(days=1)

    stocks = Stock.objects.all()

    for stock in stocks:
        print(stock.stock_code)
        if StockRecord.objects.filter(stock=stock, date=twdt.date()).count() == 0:
            try:
                kbars = api.kbars(
                    contract=api.Contracts.Stocks[stock.stock_code], start=start_date)
                df = pd.DataFrame({**kbars})
                df.ts = pd.to_datetime(df.ts)
                # df
                # 分K轉成日K
                df.set_index(df.ts, inplace=True)
                df = df.resample('D').agg(
                    {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
                df.dropna(inplace=True)
                for index, row in df.iterrows():
                    try:
                        if StockRecord.objects.filter(stock=stock, date=row.name.date()).count() == 0:
                            stockRecord = StockRecord()
                        else:
                            stockRecord = StockRecord.objects.filter(
                                stock=stock, date=row.name.date()).first()
                        if stockRecord.stock != None and stockRecord.date != None and stockRecord.OpeningPrice != None and stockRecord.ClosingPrice != None and stockRecord.DayHigh != None and stockRecord.DayLow != None and stockRecord.Volume != None:
                            pass

                        else:
                            stockRecord.stock = stock
                            stockRecord.date = row.name.date()
                            stockRecord.OpeningPrice = round(
                                Decimal(row.Open), 2)
                            stockRecord.ClosingPrice = round(
                                Decimal(row.Close), 2)
                            stockRecord.DayHigh = round(Decimal(row.High), 2)
                            stockRecord.DayLow = round(Decimal(row.Low), 2)
                            stockRecord.Volume = round(Decimal(row.Volume), 2)
                            stockRecord.save()
                    except:
                        pass

            except:
                pass
        if StockRecord.objects.get(stock=stock, date=twdt.date()).count != 0:
            print(StockRecord.objects.get(stock=stock, date=twdt.date()))

    api.logout()  # 登出


def add_user():
    User.objects.create(password='scott0815',
                        email='scottman608@gmail', name='Scott')
