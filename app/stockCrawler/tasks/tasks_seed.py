# from stockCore.models import KeyValueIndex, FilterCondition, UserFilterCondition, User, InterestRate, Stock
from stockCore.models import User,Stock ,StockRecord
import shioaji as sj # 載入永豐金Python API
import pandas as pd
from datetime import date, datetime, timedelta ,timezone
import pytz
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Avg ,Sum 
import csv
import os
import decimal
from django.db.models import Avg ,Sum 


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
    from stockCore.models import User,Stock ,StockRecord
    user = User.objects.get(id=2)
    print(user)
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = user.PERSON_ID #身分證字號
    PASSWORD = user.account_password #密碼
    api.login(PERSON_ID, PASSWORD) # 登入

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

    start_date = '2022-04-01'
    end_date = '2022-07-01'
    if weekday == 0:
        EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=3)
    else:
        EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=1)
        
    stocks = Stock.objects.all()
    for stock in stocks:
        print(stock.stock_code)
        if StockRecord.objects.filter(stock=stock,date=datetime.strptime('2022-06-30', '%Y-%m-%d').date()).count() != 0 :
            pass
        else:
            try:
                kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = start_date,end=end_date)
                df = pd.DataFrame({**kbars})
                df.ts = pd.to_datetime(df.ts)
                # df
                #分K轉成日K
                df.set_index(df.ts,inplace=True)
                df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume':'sum'})
                df.dropna(inplace=True)
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
                        pass
                # EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=1)
                # stockRecords = StockRecord.objects.filter(stock=stock,date__lte=end_date).order_by('-date')
                # for stockRecord in stockRecords:
                #     if stockRecords.filter(date__lte=stockRecord.date).count() == 12:
                #         stockRecords_12 = stockRecord
                #         if stockRecords.filter(date=stockRecords_12.date,EMA_12__isnull=False).count() == 0:
                #             stockRecords_12.EMA_12 = stockRecords_12.MA_12
                #             stockRecords_12.save()
                #     if stockRecords.filter(date__lte=stockRecord.date).count() == 26:
                #         stockRecords_26 = stockRecord
                #         if stockRecords.filter(date=stockRecords_26.date,EMA_26__isnull=False).count() == 0:
                #             stockRecords_26.EMA_26 = stockRecords_26.MA_26
                #             stockRecords_26.save()
                # stockRecords_12_list = list(stockRecords.filter(date__gte=EMA_start_date).order_by('date'))
                # for i in range(1,len(stockRecords_12_list)):
                #     if stockRecords.filter(date=stockRecords_12_list[i].date,EMA_12__isnull=False).count() == 0:
                #         # cdp = (stockRecords_12_list[i].DayHigh + stockRecords_12_list[i].DayLow + (stockRecords_12_list[i].ClosingPrice * 2))/4
                #         # print('cdp:',cdp)
                #         ema12 = round((stockRecords_12_list[i].ClosingPrice * round(decimal.Decimal(2/13),2)) + (stockRecords_12_list[i-1].EMA_12)*(1-round(decimal.Decimal(2/13),2)),2)
                #         stockRecords_12_list[i].EMA_12 = ema12
                #         stockRecords_12_list[i].save()
                    
                
                # stockRecords_26_list = list(stockRecords.filter(date__gte=EMA_start_date).order_by('date'))
                
                # for i in range(1,len(stockRecords_26_list)):
                #     if (stockRecords.filter(date=stockRecords_26_list[i].date,EMA_26__isnull=False).count() == 0) | (stockRecords.filter(date=stockRecords_26_list[i].date,DIF__isnull=False).count() == 0):
                #         stockRecords_26_list[i].EMA_26 = round(decimal.Decimal(stockRecords_26_list[i].ClosingPrice * round(decimal.Decimal(2/27),2)) + (stockRecords_26_list[i-1].EMA_26)*(1-round(decimal.Decimal(2/27),2)),2)
                #         stockRecords_26_list[i].DIF = stockRecords_26_list[i].EMA_12 - stockRecords_26_list[i].EMA_26
                #         stockRecords_26_list[i].save()

                # for stockRecord in stockRecords:
                #     if stockRecords.filter(date__lte=stockRecord.date,DIF__isnull=False).count() == 9:
                #         stockRecords_MACD_9 = stockRecord
                #         # if stockRecords.filter(date=stockRecords_MACD_9.date,MACD__isnull=False).count() == 0:
                #         MACD_9 = stockRecords.filter(DIF__isnull=False).order_by('date')[:9].aggregate(Avg('DIF'))['DIF__avg']
                #         stockRecords_MACD_9.MACD = MACD_9
                #         stockRecords_MACD_9.save()

                # stockRecords_MACD_list = list(stockRecords.filter(DIF__isnull=False,date__gte=EMA_start_date).order_by('date'))
                # for i in range(1,len(stockRecords_MACD_list)):
                #     if stockRecords.filter(date=stockRecords_MACD_list[i].date,MACD__isnull=False).count() == 0:
                #         stockRecords_MACD_list[i].MACD = round(decimal.Decimal(stockRecords_MACD_list[i-1].MACD + round(decimal.Decimal(2/10),2)*(stockRecords_MACD_list[i].DIF-stockRecords_MACD_list[i-1].MACD)),2)
                #         stockRecords_MACD_list[i].save()

            except:
                # print(stock.name + " " + stock.stock_code  + " no index data.")
                pass

            

    api.logout() # 登出

