import os
from celery import Celery
from celery.schedules import crontab
from datetime import date, datetime, timedelta ,timezone
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
        crontab(hour=8, minute=40, day_of_week='1-5'),
        get_stock_datas.s('crawl today stock record'),
    )

    sender.add_periodic_task(
        crontab(hour=8, minute=53, day_of_week='1-5'),
        get_stock_day_recommend.s('get today stock recommend'),
    )

    sender.add_periodic_task(
        crontab(hour=8, minute=55),
        get_recent_N_font_stock.s('get recent N font type stock'),
    )


@app.task
def test(arg):
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(dt_string)

@app.task
def get_stock_datas(arg):
    from stockCore.models import User,Stock ,StockRecord
    user = User.objects.get(id=2)
    sj.__version__ # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
    PERSON_ID = user.PERSON_ID #身分證字號
    PASSWORD = user.account_password #密碼
    api.login(PERSON_ID, PASSWORD) # 登入

    # start_date = '20' + (date.today() - timedelta(days=2)).strftime("%y-%m-%d")
    weekday = datetime.utcnow().replace(tzinfo=timezone.utc).weekday()
    if weekday == 5:
        start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif weekday == 6:
        start_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    stocks = Stock.objects.all()
    for stock in stocks:
        # if (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=5))).count() == 0) and (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=2))).count() == 0):
            try:
                kbars =api.kbars(contract=api.Contracts.Stocks[stock.stock_code], start = start_date )
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
            
                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20 ) and (stockRecords_list[6].MA_20  < stockRecords_list[12].MA_20 ) :
                    def hold(stockRecords_list):
                        if ((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice) & (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice > stockRecords_list[1].OpeningPrice ) & (stockRecords_list[0].OpeningPrice < stockRecords_list[1].ClosingPrice)) :
                            return True

                    def childparent(stockRecords_list):
                        if((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice)& (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice < stockRecords_list[1].OpeningPrice) & (stockRecords_list[0].OpeningPrice > stockRecords_list[1].ClosingPrice)):
                            return True
                    
                    if (hold(stockRecords_list)  == True) | (childparent(stockRecords_list) == True):
                        if StockDayRecommend.objects.filter(stock=stock,date=stockRecords_list[0].date,type=KbarsType.objects.get(id=1)).count() == 0:
                            StockDayRecommend.objects.create(stock=stock,date=stockRecords_list[0].date,type=KbarsType.objects.get(id=1))
                        return True
                    else:
                        return False
                else:
                    return False

            def longShadeLine(stockRecords_list):

                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20 ) and (stockRecords_list[6].MA_20  < stockRecords_list[12].MA_20 ) :
                    if (0 < ((stockRecords_list[0].OpeningPrice - stockRecords_list[0].ClosingPrice)/stockRecords_list[0].OpeningPrice) < 0.01) & (((stockRecords_list[0].ClosingPrice - stockRecords_list[0].DayLow)/stockRecords_list[0].ClosingPrice) > 0.03) & (((stockRecords_list[0].DayHigh - stockRecords_list[0].OpeningPrice)/stockRecords_list[0].OpeningPrice) < 0.005):
                        if StockDayRecommend.objects.filter(stock=stock,date=stockRecords_list[0].date,type=KbarsType.objects.get(id=2)).count() == 0:
                            StockDayRecommend.objects.create(stock=stock,date=stockRecords_list[0].date,type=KbarsType.objects.get(id=2))
                        return True
                    else:
                        return False
                else:
                    return False

            childparent_choose = strategy(stockRecords_list)
            longShadeLine_choose = longShadeLine(stockRecords_list)
            if childparent_choose == True:
                childparent_list.append(stock.stock_code)
                

            if longShadeLine_choose == True:
                longShadeLine_list.append(stock.stock_code)
                
        except:
            pass

    buy_data = {'childparent':childparent_list,
            'longShadeLine':longShadeLine_list}

    print(buy_data)


@app.task
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
                for last_N_days in range(25,-1,-1):
                    if stock.name == 'F-立凱':
                        print(last_N_days,stockRecords_list[last_N_days].date,stockRecords_list[last_N_days].MA_60,stockRecords_list[last_N_days].ClosingPrice)
                    if (stockRecords_list[last_N_days+1].MA_60 > stockRecords_list[last_N_days+1].ClosingPrice ) and (stockRecords_list[last_N_days].MA_60  < stockRecords_list[last_N_days].ClosingPrice ) :              
                        # if (((stockRecords_list[last_N_days].ClosingPrice - stockRecords_list[last_N_days+2].ClosingPrice)/stockRecords_list[last_N_days+2].OpeningPrice) >= 0.1) : 
                        find_Early_stage = True
                        break
                if find_Early_stage == True:

                    Early_Stage_end_date = ''
                    for Early_Stage_end_days in range(5,15):
                        if last_N_days - Early_Stage_end_days  >= 0:
                            high_price_list = []
                            for day in Early_Stage_end_days:
                                high_price_list.append(stockRecords_list[last_N_days-day].DayHigh)
                            high_price = max(high_price_list)
                            print(high_price,)
                            high_price_index = high_price_list.index(high_price)
                            if ((high_price - stockRecords_list[last_N_days].ClosingPrice)/stockRecords_list[last_N_days].ClosingPrice) >= 0.1 :
                                Early_Stage_end_date = last_N_days - high_price_index 
                                Early_Stage_high_price = stockRecords_list[Early_Stage_end_date].DayHigh
                                Early_Stage_correction_start_at = stockRecords_list[Early_Stage_end_date].date
                                print(stock.stock_code,stock,high_price,high_price_index)
                                break
                        else:       
                            break

                    # for Early_Stage_start_days in range(0,10):

                    #     if (stockRecords_list[last_N_days+Early_Stage_start_days].OpeningPrice > stockRecords_list[last_N_days+Early_Stage_start_days].ClosingPrice):
                    #         Early_Stage_start_date = last_N_days + Early_Stage_start_days -1
                    #         break
                    Early_Stage_start_price = stockRecords_list[last_N_days].OpeningPrice
                    Early_Stage_start_at = stockRecords_list[last_N_days].date
                    
                    if N_Font_Type_Stock.objects.filter(stock=stock,Early_Stage_start_at = Early_Stage_start_at).count() == 0:

                        N_type_stock = N_Font_Type_Stock()
                        N_type_stock.stock=stock
                        N_type_stock.Early_Stage_start_at = Early_Stage_start_at
                        N_type_stock.Early_Stage_start_price = Early_Stage_start_price

                        if Early_Stage_end_date != '':
                            N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                            N_type_stock.Early_Stage_correction_start_at = Early_Stage_correction_start_at
                            
                        N_type_stock.save()
                        N_font_list.append(stock.stock_code)
                    else:
                        N_type_stock = N_Font_Type_Stock.objects.get(stock=stock,Early_Stage_start_at = Early_Stage_start_at)
                        N_type_stock.Early_Stage_start_price = Early_Stage_start_price
                        N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                        if Early_Stage_end_date != '':
                            N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                            N_type_stock.Early_Stage_correction_start_at = Early_Stage_correction_start_at
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