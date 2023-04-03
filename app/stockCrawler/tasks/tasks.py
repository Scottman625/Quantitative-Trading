from os import replace
from celery import shared_task
from requests.api import put
from stockCore.models import Stock,  Category, StockRecord, Index
from datetime import date, datetime, timedelta, timezone
import pytz
import pandas as pd
import shioaji as sj  # 載入永豐金Python API
from decimal import Decimal
from requests.auth import HTTPProxyAuth
import decimal
from django.db.models import Avg, Sum


@shared_task
def get_stock_datas(arg):
    from stockCore.models import User, Stock, StockRecord
    user = User.objects.get(id=1)
    print(sj.__version__)  # 版本為 "0.3.6.dev3"
    sj.__version__  # 版本為 "0.3.6.dev3"
    api = sj.Shioaji(simulation=False)  # simulation=False 即表示使用正式環境
    api.login(user.API_Key, user.Secret_Key)  # 登入
    print('test')
    # tw = pytz.timezone('Asia/Taipei')
    # twdt = tw.localize(datetime.now())
    # weekday = twdt.weekday()
    # if twdt.hour < 13:
    #     weekday = weekday - 1
    # if weekday == 5:
    #     start_date = (twdt.date() - timedelta(days=1)).strftime("%Y-%m-%d")

    # elif weekday == 6:
    #     start_date = (twdt.date() - timedelta(days=2)).strftime("%Y-%m-%d")
    # elif weekday == -1:
    #     start_date = (twdt.date() - timedelta(days=3)).strftime("%Y-%m-%d")
    # else:
    #     start_date = twdt.date().strftime("%Y-%m-%d")

    # if weekday == 0:
    #     EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=3)
    # else:
    #     EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=1)
    start_date = (StockRecord.objects.filter(stock=Stock.objects.get(
        stock_code='6689'), MACD__isnull=False).order_by('-date').first().date).strftime("%Y-%m-%d")
    EMA_start_date = StockRecord.objects.filter(stock=Stock.objects.get(
        stock_code='6689'), MACD__isnull=False).order_by('-date').first().date
    stocks = Stock.objects.all()
    print(EMA_start_date)
    for stock in stocks:
        # if (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=5)),MACD__isnull=False).count() == 0) and (StockRecord.objects.filter(stock=stock,date=(date.today() - timedelta(days=2)),MACD__isnull=False).count() == 0):
        try:
            kbars = api.kbars(
                contract=api.Contracts.Stocks[stock.stock_code], start="2022-01-01")
            df = pd.DataFrame({**kbars})
            df.ts = pd.to_datetime(df.ts)
            # df
            # 分K轉成日K
            df.set_index(df.ts, inplace=True)
            df = df.resample('D').agg(
                {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
            df.dropna(inplace=True)
            print(stock.stock_code)
            for index, row in df.iterrows():
                try:
                    if StockRecord.objects.filter(stock=stock, date=row.name.date()).count() == 0:
                        stockRecord = StockRecord()
                    else:
                        stockRecord = StockRecord.objects.filter(
                            stock=stock, date=row.name.date()).first()
                    stockRecord.stock = stock
                    stockRecord.date = row.name.date()
                    stockRecord.OpeningPrice = round(Decimal(row.Open), 2)
                    stockRecord.ClosingPrice = round(Decimal(row.Close), 2)
                    stockRecord.DayHigh = round(Decimal(row.High), 2)
                    stockRecord.DayLow = round(Decimal(row.Low), 2)
                    stockRecord.Volume = round(Decimal(row.Volume), 2)
                    stockRecord.save()
                except:
                    pass
            # EMA_start_date = datetime.strptime(start_date,"%Y-%m-%d").date() - timedelta(days=1)
            stockRecords = StockRecord.objects.filter(
                stock=stock).order_by('-date')
            stockRecords_12_list = list(stockRecords.filter(
                date__gte=EMA_start_date).order_by('date'))
            for i in range(1, len(stockRecords_12_list)):
                if stockRecords.filter(date=stockRecords_12_list[i].date, EMA_12__isnull=False).count() == 0:
                    # cdp = (stockRecords_12_list[i].DayHigh + stockRecords_12_list[i].DayLow + (stockRecords_12_list[i].ClosingPrice * 2))/4
                    # print('cdp:',cdp)
                    ema12 = round((stockRecords_12_list[i].ClosingPrice * round(decimal.Decimal(2/13), 2)) + (
                        stockRecords_12_list[i-1].EMA_12)*(1-round(decimal.Decimal(2/13), 2)), 2)
                    print(stockRecords_12_list[i])
                    stockRecords_12_list[i].EMA_12 = ema12
                    stockRecords_12_list[i].save()

            stockRecords_26_list = list(stockRecords.filter(
                date__gte=EMA_start_date).order_by('date'))

            for i in range(1, len(stockRecords_26_list)):
                if (stockRecords.filter(date=stockRecords_26_list[i].date, EMA_26__isnull=False).count() == 0) | (stockRecords.filter(date=stockRecords_26_list[i].date, DIF__isnull=False).count() == 0):
                    stockRecords_26_list[i].EMA_26 = round(decimal.Decimal(stockRecords_26_list[i].ClosingPrice * round(
                        decimal.Decimal(2/27), 2)) + (stockRecords_26_list[i-1].EMA_26)*(1-round(decimal.Decimal(2/27), 2)), 2)
                    stockRecords_26_list[i].DIF = stockRecords_26_list[i].EMA_12 - \
                        stockRecords_26_list[i].EMA_26
                    stockRecords_26_list[i].save()

            stockRecords_MACD_list = list(stockRecords.filter(
                DIF__isnull=False, date__gte=EMA_start_date).order_by('date'))
            for i in range(1, len(stockRecords_MACD_list)):
                if stockRecords.filter(date=stockRecords_MACD_list[i].date, MACD__isnull=False).count() == 0:
                    stockRecords_MACD_list[i].MACD = round(decimal.Decimal(stockRecords_MACD_list[i-1].MACD + round(
                        decimal.Decimal(2/10), 2)*(stockRecords_MACD_list[i].DIF-stockRecords_MACD_list[i-1].MACD)), 2)
                    stockRecords_MACD_list[i].save()

        except:
            # print(stock.name + " " + stock.stock_code  + " no index data.")
            pass

    api.logout()  # 登出


@shared_task
def get_stock_day_recommend(args):
    from stockCore.models import User, Stock, StockRecord, StockDayRecommend, KbarsType
    stocks = Stock.objects.all()
    childparent_list = []
    longShadeLine_list = []
    for stock in stocks:
        try:
            stockRecords = StockRecord.objects.filter(
                stock=stock).order_by('-date')
            stockRecords_list = list(stockRecords)
            # print(stockRecords_list)
            # print(type(stockRecords_list[-1].MA_20),stockRecords_list[-1].MA_20)

            def strategy(stockRecords_list):

                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20) and (stockRecords_list[6].MA_20 < stockRecords_list[12].MA_20):
                    def hold(stockRecords_list):
                        if ((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice) & (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice > stockRecords_list[1].OpeningPrice) & (stockRecords_list[0].OpeningPrice < stockRecords_list[1].ClosingPrice)):
                            return True

                    def childparent(stockRecords_list):
                        if ((stockRecords_list[1].OpeningPrice > stockRecords_list[1].ClosingPrice) & (stockRecords_list[0].OpeningPrice < stockRecords_list[0].ClosingPrice)) & ((stockRecords_list[0].ClosingPrice < stockRecords_list[1].OpeningPrice) & (stockRecords_list[0].OpeningPrice > stockRecords_list[1].ClosingPrice)):
                            return True

                    if (hold(stockRecords_list) == True) | (childparent(stockRecords_list) == True):
                        if StockDayRecommend.objects.filter(stock=stock, date=stockRecords_list[0].date, type=KbarsType.objects.get(id=1)).count() == 0:
                            StockDayRecommend.objects.create(
                                stock=stock, date=stockRecords_list[0].date, type=KbarsType.objects.get(id=1))
                        return True
                    else:
                        return False
                else:
                    return False

            def longShadeLine(stockRecords_list):

                if (stockRecords_list[0].MA_20 < stockRecords_list[6].MA_20) and (stockRecords_list[6].MA_20 < stockRecords_list[12].MA_20):
                    if (0 < ((stockRecords_list[0].OpeningPrice - stockRecords_list[0].ClosingPrice)/stockRecords_list[0].OpeningPrice) < 0.01) & (((stockRecords_list[0].ClosingPrice - stockRecords_list[0].DayLow)/stockRecords_list[0].ClosingPrice) > 0.03) & (((stockRecords_list[0].DayHigh - stockRecords_list[0].OpeningPrice)/stockRecords_list[0].OpeningPrice) < 0.005):
                        if StockDayRecommend.objects.filter(stock=stock, date=stockRecords_list[0].date, type=KbarsType.objects.get(id=2)).count() == 0:
                            StockDayRecommend.objects.create(
                                stock=stock, date=stockRecords_list[0].date, type=KbarsType.objects.get(id=2))
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

    buy_data = {'childparent': childparent_list,
                'longShadeLine': longShadeLine_list}

    print(buy_data)


@shared_task
def get_recent_N_font_stock(args):
    from stockCore.models import User, Stock, StockRecord, StockDayRecommend, KbarsType, N_Font_Type_Stock
    stocks = Stock.objects.all()
    N_font_list = []
    red_sign_list = []
    tw = pytz.timezone('Asia/Taipei')
    twdt = tw.localize(datetime.now())
    for stock in stocks:
        try:
            stockRecords = StockRecord.objects.filter(
                stock=stock).order_by('-date')
            stockRecords_list = list(stockRecords)

            def find_N_font_type(stockRecords_list):
                find_Early_stage = False
                for last_N_days in range(25, -1, -1):

                    if (stockRecords_list[last_N_days+1].MA_60 > stockRecords_list[last_N_days+1].ClosingPrice) and (stockRecords_list[last_N_days].MA_60 < stockRecords_list[last_N_days].ClosingPrice) and (stockRecords_list[last_N_days].Volume > 200):
                        # if (((stockRecords_list[last_N_days].ClosingPrice - stockRecords_list[last_N_days+2].ClosingPrice)/stockRecords_list[last_N_days+2].OpeningPrice) >= 0.1) :
                        for Early_Stage_start_days in range(5, -5, -1):
                            if last_N_days + Early_Stage_start_days >= 0:
                                if (stockRecords_list[last_N_days + Early_Stage_start_days + 1].MACD < 0) and (stockRecords_list[last_N_days + Early_Stage_start_days].MACD > 0):
                                    find_Early_stage = True
                                    start_date = last_N_days + Early_Stage_start_days
                                    Early_Stage_start_date = stockRecords_list[start_date].date
                                    break
                            else:
                                continue
                if find_Early_stage == True:
                    Early_Stage_end_date = None
                    red_sign_start_at = None
                    for Early_Stage_end_days in range(20):
                        if start_date - Early_Stage_end_days >= 0:
                            if (stockRecords_list[start_date - Early_Stage_end_days + 1].OSC < 0) and (stockRecords_list[start_date - Early_Stage_end_days].OSC > 0):
                                red_sign_start_at = stockRecords_list[start_date -
                                                                      Early_Stage_end_days].date
                                if StockDayRecommend.objects.filter(stock=stock, date=red_sign_start_at, type=KbarsType.objects.get(id=4)).count() == 0:
                                    StockDayRecommend.objects.create(
                                        stock=stock, date=red_sign_start_at, type=KbarsType.objects.get(id=4))

                            high_price_list = []
                            for day in range(Early_Stage_end_days + 1):
                                high_price_list.append(
                                    stockRecords_list[start_date-day].DayHigh)

                            high_price = max(high_price_list)

                            high_price_index = high_price_list.index(
                                high_price)
                            if ((high_price - stockRecords_list[start_date].ClosingPrice)/stockRecords_list[start_date].ClosingPrice) >= 0.1:
                                Early_Stage_end_date = start_date - high_price_index
                                Early_Stage_high_price = stockRecords_list[Early_Stage_end_date].DayHigh
                                Early_Stage_correction_start_at = stockRecords_list[
                                    Early_Stage_end_date].date

                                break
                        else:
                            continue

                    Early_Stage_start_price = stockRecords_list[start_date].DayLow
                    Early_Stage_start_at = Early_Stage_start_date
                    if N_Font_Type_Stock.objects.filter(stock=stock, red_sign_start_at__gte=(twdt.date() - timedelta(days=3))).count() != 0:
                        red_sign_list.append(
                            {'股票名稱': stock.name, '股票代號': stock.stock_code, '日期': red_sign_start_at})

                    if N_Font_Type_Stock.objects.filter(stock=stock, Early_Stage_start_at=Early_Stage_start_at).count() == 0:
                        N_type_stock = N_Font_Type_Stock()
                        N_type_stock.stock = stock
                        N_type_stock.Early_Stage_start_at = Early_Stage_start_at
                        N_type_stock.Early_Stage_start_price = Early_Stage_start_price
                        if red_sign_start_at != None:
                            N_type_stock.red_sign_start_at = red_sign_start_at
                            print(
                                f'股票名稱:{stock.name},股票代號:{stock.stock_code},日期:{red_sign_start_at}')
                        if Early_Stage_end_date != None:
                            N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                            N_type_stock.Early_Stage_correction_start_at = Early_Stage_correction_start_at

                        N_type_stock.save()
                        N_font_list.append(stock.stock_code)
                    else:
                        N_type_stock = N_Font_Type_Stock.objects.get(
                            stock=stock, Early_Stage_start_at=Early_Stage_start_at)
                        N_type_stock.Early_Stage_start_price = Early_Stage_start_price
                        N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                        if red_sign_start_at != None:
                            N_type_stock.red_sign_start_at = red_sign_start_at
                            print(
                                f'股票名稱:{stock.name},股票代號:{stock.stock_code},日期:{red_sign_start_at}')
                        if Early_Stage_end_date != None:
                            N_type_stock.Early_Stage_high_price = Early_Stage_high_price
                            N_type_stock.Early_Stage_correction_start_at = Early_Stage_correction_start_at
                        N_type_stock.save()

                    return True

                else:
                    return False

            N_font_type_choose = find_N_font_type(stockRecords_list)
            if twdt.hour < 14:
                weekday = weekday - 1
            if weekday == 5:
                last_trade_date = twdt.date() - timedelta(days=2)
            elif weekday == 6:
                last_trade_date = twdt.date() - timedelta(days=3)
            else:
                last_trade_date = twdt.date() - timedelta(days=1)
            if N_font_type_choose == True:
                if StockDayRecommend.objects.filter(stock=stock, date=last_trade_date, type=KbarsType.objects.get(id=3)).count() > 0:
                    day_rec = StockDayRecommend.objects.get(
                        stock=stock, date=last_trade_date, type=KbarsType.objects.get(id=3))
                    day_rec.date = twdt.date()
                    day_rec.save()

        except:
            pass

    print(N_font_list)
    print(red_sign_list)


@shared_task
def calculate_EMA(args):
    from stockCore.models import User, Stock, StockRecord
    stocks = Stock.objects.all()
    tw = pytz.timezone('Asia/Taipei')
    twdt = tw.localize(datetime.now())
    for stock in stocks:
        print(stock.stock_code)
        if StockRecord.objects.filter(stock=stock, date=twdt.date(), DIF__isnull=False).count() != 0:
            pass
        else:
            try:
                stockRecords = StockRecord.objects.filter(
                    stock=stock).order_by('-date')
                for stockRecord in stockRecords:
                    if stockRecords.filter(date__lte=stockRecord.date).count() == 12:
                        stockRecords_12 = stockRecord
                        if stockRecords.filter(date=stockRecords_12.date, EMA_12__isnull=False).count() == 0:
                            stockRecords_12.EMA_12 = stockRecords_12.MA_12
                            stockRecords_12.save()
                    if stockRecords.filter(date__lte=stockRecord.date).count() == 26:
                        stockRecords_26 = stockRecord
                        if stockRecords.filter(date=stockRecords_26.date, EMA_26__isnull=False).count() == 0:
                            stockRecords_26.EMA_26 = stockRecords_26.MA_26
                            stockRecords_26.save()

                stockRecords_12_list = list(stockRecords.filter(
                    date__gte=stockRecords_12.date).order_by('date'))
                for i in range(1, len(stockRecords_12_list)):
                    if stockRecords.filter(date=stockRecords_12_list[i].date, EMA_12__isnull=False).count() == 0:
                        # cdp = (stockRecords_12_list[i].DayHigh + stockRecords_12_list[i].DayLow + (stockRecords_12_list[i].ClosingPrice * 2))/4
                        # print('cdp:',cdp)
                        ema12 = round((stockRecords_12_list[i].ClosingPrice * round(decimal.Decimal(2/13), 2)) + (
                            stockRecords_12_list[i-1].EMA_12)*(1-round(decimal.Decimal(2/13), 2)), 2)

                        stockRecords_12_list[i].EMA_12 = ema12
                        stockRecords_12_list[i].save()

                stockRecords_26_list = list(stockRecords.filter(
                    date__gte=stockRecords_26.date).order_by('date'))

                for i in range(1, len(stockRecords_26_list)):
                    if (stockRecords.filter(date=stockRecords_26_list[i].date, EMA_26__isnull=False).count() == 0) | (stockRecords.filter(date=stockRecords_26_list[i].date, DIF__isnull=False).count() == 0):
                        EMA_26 = round(decimal.Decimal(stockRecords_26_list[i].ClosingPrice * round(decimal.Decimal(
                            2/27), 2)) + (stockRecords_26_list[i-1].EMA_26)*(1-round(decimal.Decimal(2/27), 2)), 2)
                        if stockRecords_26_list[i].EMA_26 != EMA_26:
                            stockRecords_26_list[i].EMA_26 = round(decimal.Decimal(stockRecords_26_list[i].ClosingPrice * round(
                                decimal.Decimal(2/27), 2)) + (stockRecords_26_list[i-1].EMA_26)*(1-round(decimal.Decimal(2/27), 2)), 2)
                            stockRecords_26_list[i].DIF = stockRecords_26_list[i].EMA_12 - stockRecords_26_list[i].EMA_26
                            stockRecords_26_list[i].save()
                        else:
                            pass

            except:
                pass

@shared_task
def calculate_MACD(args):
    from stockCore.models import User, Stock, StockRecord
    stocks = Stock.objects.all()
    tw = pytz.timezone('Asia/Taipei')
    twdt = tw.localize(datetime.now())
    for stock in stocks:
        print(stock.stock_code)
        if StockRecord.objects.filter(stock=stock, date=twdt.date(), MACD__isnull=False).count() != 0:
            pass
        else:
            try:
                stockRecords = StockRecord.objects.filter(
                    stock=stock).order_by('-date')
                for stockRecord in stockRecords:
                    if stockRecords.filter(date__lte=stockRecord.date, DIF__isnull=False).count() == 9:
                        stockRecords_MACD_9 = stockRecord
                        # if stockRecords.filter(date=stockRecords_MACD_9.date,MACD__isnull=False).count() == 0:
                        MACD_9 = stockRecords.filter(DIF__isnull=False).order_by('date')[
                            :9].aggregate(Avg('DIF'))['DIF__avg']
                        stockRecords_MACD_9.MACD = MACD_9
                        stockRecords_MACD_9.save()

                stockRecords_MACD_list = list(stockRecords.filter(
                    DIF__isnull=False, date__gte=stockRecords_MACD_9.date).order_by('date'))
                for i in range(1, len(stockRecords_MACD_list)):
                    # if stockRecords.filter(date=stockRecords_MACD_list[i].date,MACD__isnull=False).count() == 0:
                    MACD = round(decimal.Decimal(stockRecords_MACD_list[i-1].MACD + round(decimal.Decimal(
                        2/10), 2)*(stockRecords_MACD_list[i].DIF-stockRecords_MACD_list[i-1].MACD)), 2)
                    if stockRecords_MACD_list[i].MACD != MACD:
                        stockRecords_MACD_list[i].MACD = round(decimal.Decimal(stockRecords_MACD_list[i-1].MACD + round(
                            decimal.Decimal(2/10), 2)*(stockRecords_MACD_list[i].DIF-stockRecords_MACD_list[i-1].MACD)), 2)
                        stockRecords_MACD_list[i].save()
                    else:
                        pass

            except:
                pass


@shared_task
def delete_data():
    from stockCore.models import N_Font_Type_Stock
    N_type_stocks = N_Font_Type_Stock.objects.filter(id__lte=632)
    N_type_stocks.delete()


@shared_task
def add_signal():
    from stockCore.models import User, Stock, StockRecord
    stocks = Stock.objects.all()
    for stock in stocks:
        print(stock.stock_code)
        try:
            stockRecords = StockRecord.objects.filter(
                stock=stock).order_by('date')
            stockRecords_list = list(stockRecords)

            for i in range(len(stockRecords_list) - 5):
                if (stockRecords_list[i+5].DayHigh - stockRecords_list[i].ClosingPrice) / (stockRecords_list[i].ClosingPrice) > 0.1:
                    stockRecords_list[i].Signal = 1
                    stockRecords_list[i].save()
                    print(stockRecords_list[i+5].date,
                          stockRecords_list[i].date)
                else:
                    if stockRecords_list[i].Signal == 1:
                        stockRecords_list[i].Signal = 0
                        stockRecords_list[i].save()

        except:
            pass
