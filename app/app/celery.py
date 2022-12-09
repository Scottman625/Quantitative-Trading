import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, date, timedelta
import shioaji as sj # 載入永豐金Python API
import pandas as pd
from decimal import Decimal
# from __future__ import absolute_import
# from celery import Celery
# app = Celery('test_celery',
#           broker='amqp://maxat:password123@localhost/maxat_vhost',
#           backend='rpc://',
#           include=['test_celery.tasks'])

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
app = Celery('celery')


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# response = app.control.enable_events(reply=True)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    # sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    # sender.add_periodic_task(60.0, send_user_notify_price_message.s('world'), expires=10)

    #server use UTC time, it should be Taiwan time -8 hour, ex 10:00am taipei task, should set 02:00am server task
    # Daily task
    # sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    #run at 1500 every Taiwan time
    sender.add_periodic_task(
        crontab(hour=6, minute=10, day_of_week='1-5'),
        get_stock_datas.s('crawl today stock record'),
    )

    sender.add_periodic_task(
        crontab(hour=10, minute=0, day_of_week='1-5'),
        get_stock_day_recommend.s('get today stock recommend'),
    )


@app.task
def test(arg):
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(dt_string)

@app.task
def get_stock_datas(arg):
    from stockCore.models import User,Stock ,StockRecord
    
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = "D122776936" #身分證字號
    PASSWORD = "Scott0815" #密碼
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
    

@app.task
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
