from os import replace
from celery import shared_task
from requests.api import put
from stockCore.models import Stock,  Category,StockRecord, Index
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
import calendar
import time
import random
import pandas as pd
import shioaji as sj # 載入永豐金Python API
from decimal import Decimal
from requests.auth import HTTPProxyAuth


@shared_task
def get_stock_datas(arg):
    from stockCore.models import User,Stock ,StockRecord
    user = User.objects.get(id=2)
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = user.PERSON_ID #身分證字號
    PASSWORD = user.account_password #密碼
    api.login(PERSON_ID, PASSWORD) # 登入

    # start_date = '20' + (date.today() - timedelta(days=2)).strftime("%y-%m-%d")
    today = date.today().strftime("%Y-%m-%d")
    stocks = Stock.objects.all()
    for stock in stocks:
        # if (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=5))).count() == 0) and (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=2))).count() == 0):
            try:
                kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = today )
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

@shared_task
def get_stock_day_recommend(args):
    from stockCore.models import User,Stock ,StockRecord ,StockDayRecommend ,KbarsType
    stocks = Stock.objects.all()
    childparent_list = []
    longShadeLine_list = []
    for stock in stocks:
        try:
            stockRecords = StockRecord.objects.filter(stock=stock).order_by('-date')
            stockRecords_list = list(stockRecords)
            # print(stockRecords_list)
            # print(type(stockRecords_list[-1].MA_20),stockRecords_list[-1].MA_20)
            def strategy(stockRecords_list):
                if stock.stock_code == '6491':
                    print(stockRecords_list[0].OpeningPrice,stockRecords_list[0].ClosingPrice,stockRecords_list[1].OpeningPrice,stockRecords_list[1].ClosingPrice)
                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20 ) and (stockRecords_list[6].MA_20  < stockRecords_list[12].MA_20 ) :
                    def hold(stockRecords_list):
                        if ((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice) & (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice > stockRecords_list[1].OpeningPrice ) & (stockRecords_list[0].OpeningPrice < stockRecords_list[1].ClosingPrice)) :
                            return True

                    def childparent(stockRecords_list):
                        if((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice)& (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice < stockRecords_list[1].OpeningPrice) & (stockRecords_list[0].OpeningPrice > stockRecords_list[1].ClosingPrice)):
                            return True
                    
                    if hold(stockRecords_list)  == True:
                        return True
                    elif childparent(stockRecords_list) == True:
                        return True
                    else:
                        return False
                else:
                    return False

            def longShadeLine(stockRecords_list):

                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20 ) and (stockRecords_list[6].MA_20  < stockRecords_list[12].MA_20 ) :
                    if (0 < ((stockRecords_list[0].OpeningPrice - stockRecords_list[0].ClosingPrice)/stockRecords_list[0].OpeningPrice) < 0.01) & (((stockRecords_list[0].ClosingPrice - stockRecords_list[0].DayLow)/stockRecords_list[0].ClosingPrice) > 0.03) & (((stockRecords_list[0].DayHigh - stockRecords_list[0].OpeningPrice)/stockRecords_list[0].OpeningPrice) < 0.005):
                        return True
                    else:
                        return False
                else:
                    return False

            childparent_choose = strategy(stockRecords_list)
            longShadeLine_choose = longShadeLine(stockRecords_list)
            if childparent_choose == True:
                childparent_list.append(stock.stock_code)
                if StockDayRecommend.objects.filter(stock=stock,date=date.today(),type=KbarsType.objects.get(id=1)).count() == 0:
                    StockDayRecommend.objects.create(stock=stock,date=date.today(),type=KbarsType.objects.get(id=1))

            if longShadeLine_choose == True:
                longShadeLine_list.append(stock.stock_code)
                if StockDayRecommend.objects.filter(stock=stock,date=date.today(),type=KbarsType.objects.get(id=2)).count() == 0:
                    StockDayRecommend.objects.create(stock=stock,date=date.today(),type=KbarsType.objects.get(id=2))
        except:
            pass

    buy_data = {'childparent':childparent_list,
            'longShadeLine':longShadeLine_list}

    print(buy_data)


@shared_task
def get_recent_N_font_stock(args):
    from stockCore.models import User,Stock ,StockRecord ,StockDayRecommend ,KbarsType ,N_Font_Type_Stock
    stocks = Stock.objects.all()
    N_font_list = []
    for stock in stocks:
        try:
            stockRecords = StockRecord.objects.filter(stock=stock).order_by('-date')
            stockRecords_list = list(stockRecords)
            def find_N_font_type(stockRecords_list):
                find_Early_stage = False
                for last_N_days in range(15,-1,-1):
                    if (stockRecords_list[last_N_days].MA_20 < stockRecords_list[last_N_days+8].MA_20 ) and (stockRecords_list[last_N_days+8].MA_20  < stockRecords_list[last_N_days+16].MA_20 ) :              
                        if (((stockRecords_list[last_N_days].ClosingPrice - stockRecords_list[last_N_days+2].ClosingPrice)/stockRecords_list[last_N_days+2].OpeningPrice) >= 0.1) : 
                            find_Early_stage = True
                            break
                if find_Early_stage == True:
                    print(stock.stock_code,'find_early_stage')
                    for Early_Stage_end_days in range(0,10):
                        if last_N_days - Early_Stage_end_days  >= 0:
                            if (stockRecords_list[last_N_days-Early_Stage_end_days].OpeningPrice > stockRecords_list[last_N_days-Early_Stage_end_days].ClosingPrice):
                                Early_Stage_end_date = last_N_days - Early_Stage_end_days +1
                                break
                        else:       
                            Early_Stage_end_date = last_N_days - Early_Stage_end_days + 2
                            break

                    for Early_Stage_start_days in range(0,10):

                        if (stockRecords_list[last_N_days+Early_Stage_start_days].OpeningPrice > stockRecords_list[last_N_days+Early_Stage_start_days].ClosingPrice):
                            Early_Stage_start_date = last_N_days + Early_Stage_start_days -1
                            break
                    Early_Stage_start_price = stockRecords_list[Early_Stage_start_date].OpeningPrice
                    Early_Stage_high_price = stockRecords_list[Early_Stage_end_date].DayHigh
                    Early_Stage_start_at = stockRecords_list[Early_Stage_start_date].date
                    if N_Font_Type_Stock.objects.filter(stock=stock,Early_Stage_start_at = Early_Stage_start_at).count() == 0:
                        N_Font_Type_Stock.objects.create(stock=stock,Early_Stage_start_at=Early_Stage_start_at,Early_Stage_start_price=Early_Stage_start_price,Early_Stage_high_price=Early_Stage_high_price)
                        N_font_list.append(stock.stock_code)
                    else:
                        N_type_stock = N_Font_Type_Stock.objects.get(stock=stock,Early_Stage_start_at = Early_Stage_start_at)
                        N_type_stock.Early_Stage_start_price = Early_Stage_start_price
                        N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                        N_type_stock.save()
                        

                    return True
                            
                else:
                    return False

            N_font_type_choose = find_N_font_type(stockRecords_list)
            if N_font_type_choose == True:
                if StockDayRecommend.objects.filter(stock=stock,date=date.today(),type=KbarsType.objects.get(id=3)).count() == 0:
                    StockDayRecommend.objects.create(stock=stock,date=date.today(),type=KbarsType.objects.get(id=3))

        except:
            pass
    
    print(N_font_list)


@shared_task
def delete_data():
    from stockCore.models import User,Stock ,StockRecord ,StockDayRecommend ,KbarsType ,N_Font_Type_Stock
    N_type_stocks = N_Font_Type_Stock.objects.filter(id__lte=50)
    N_type_stocks.delete()
