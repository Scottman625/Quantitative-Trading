from celery import shared_task
from stockCore.models import Stock, StockRecord
from datetime import datetime
from bs4 import BeautifulSoup
import json
import requests
import time


@shared_task
def crawl_the_day_tpex_stock_price(date_string):
    
    the_date = datetime.strptime(date_string, '%Y%m%d')
    date_string = str(the_date.year - 1911) + the_date.strftime('/%m/%d')    
    #date_string ex. 110/05/03

    # url = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d=110/05/31&_=" + str(int(time.time()*1000))
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&o=htm&d={date_string}&s=0,asc,0"
    print(url)

    # payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    # resp = requests.get('http://api.scraperapi.com', params=payload)

    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    #date_info
    # print(soup.find_all('tr')[0].getText().replace('\n','').replace('\xa0', ' '))
    # date = soup.find_all('tr')[0].getText().replace('\n','').split(':')[1]
    # date_array = date.split('/')
    # date = str(int(date_array[0])+1911)+date_array[1]+date_array[2]

    childs = soup.find_all('tr')
    for child in childs:
        item = child.find_all('td')
        # print(item[1].getText() + ' length ' + str(len(item)) )

        if (len(item) == 19 or len(item) == 17) and len(item[0].getText()) == 4:

            # print(item[1].getText())

            if(Stock.objects.filter(stock_code=item[0].getText()).count() == 0):
                stock = Stock(stock_code=item[0].getText(),name=item[1].getText())
                stock.save()
            else:
                stock = Stock.objects.filter(stock_code=item[0].getText())[0]
                while Stock.objects.filter(stock_code=item[0].getText()).count() > 1:
                    Stock.objects.filter(stock_code=item[0].getText())[1].delete()

            if StockRecord.objects.filter(date=the_date,stock=stock).count() == 0:
                if(len(item) == 19):
                    try:
                        stockRecord = StockRecord(
                            stock=stock,
                            date=the_date,
                            Volume=float(item[8].getText().replace(',','')),
                            Transaction=int(item[10].getText().replace(',','')),
                            TurnOver=float(item[9].getText().replace(',','')),
                            OpeningPrice=float(item[4].getText()),
                            DayHigh=float(item[5].getText()),
                            DayLow=float(item[6].getText()),
                            ClosingPrice=float(item[2].getText()),
                            Dir=item[3].getText()[0],
                            Change=float(item[3].getText()[1:]),
                            FinalBuyPrice=float(item[11].getText()),
                            FinalBuyVolume=int(item[12].getText().replace(',','')),
                            FinalSellPrice=float(item[13].getText()),
                            FinalSellVolume=int(item[14].getText().replace(',',''))
                        )
                        stockRecord.save()
                    except:
                        print(item[1].getText() + 'length 19 the stock data went wrong')
                elif(len(item) == 17):
                    try:
                        stockRecord = StockRecord(
                            stock=stock,
                            date=the_date,
                            Volume=float(item[8].getText().replace(',','')),
                            Transaction=int(item[10].getText().replace(',','')),
                            TurnOver=float(item[9].getText().replace(',','')),
                            OpeningPrice=float(item[4].getText()),
                            DayHigh=float(item[5].getText()),
                            DayLow=float(item[6].getText()),
                            ClosingPrice=float(item[2].getText()),
                            Dir=item[3].getText()[0],
                            Change=float(item[3].getText()[1:]),
                            FinalBuyPrice=float(item[11].getText()),
                            FinalSellPrice=float(item[12].getText()),
                        )
                        stockRecord.save()
                    except:
                        print(item[1].getText() + 'length 17 the stock data went wrong')

    # time.sleep(2)

# @shared_task
# def crawl_history_tpex_stock_price_after_960420():
#     if StockRecord.objects.all().count() != 0:
#         #以 3293 沁象為基準
#         stock = Stock.objects.get(stock_code='3293')
#         stockRecord = StockRecord.objects.filter(stock=stock).order_by('-date')[0]
#         start_date = stockRecord.date
#     else:
#         start_date = datetime(2007, 4, 20)

#     end_date = datetime.today()
#     delta = timedelta(days=1)

#     while start_date < end_date:
#         date_string = str(the_date.year - 1911) + the_date.strftime('/%m/%d')

#         url = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&o=htm&d={date_string}&s=0,asc,0"
#         print(url)

#         resp = requests.get(url)
#         soup = BeautifulSoup(resp.text, 'html.parser')
        
#         childs = soup.find_all('tr')
#         for child in childs:
#             item = child.find_all('td')
#             if (len(item) == 19 and len(item[0].getText()) == 4):
                
#                 print(item[1].getText())

#                 if(Stock.objects.filter(stock_code=item[0].getText()).count() == 0):
#                     stock = Stock(stock_code=item[0].getText(),name=item[1].getText())
#                     stock.save()
#                 else:
#                     stock = Stock.objects.get(stock_code=item[0].getText())
                
#                 if StockRecord.objects.filter(date=start_date,stock=stock).count() == 0:
#                     try:
#                         stockRecord = StockRecord(
#                             stock=stock,
#                             date=start_date,
#                             Volume=float(item[8].getText().replace(',','')),
#                             Transaction=int(item[10].getText().replace(',','')),
#                             TurnOver=float(item[9].getText().replace(',','')),
#                             OpeningPrice=float(item[4].getText()),
#                             DayHigh=float(item[5].getText()),
#                             DayLow=float(item[6].getText()),
#                             ClosingPrice=float(item[2].getText()),
#                             Dir=item[3].getText()[0],
#                             Change=float(item[3].getText()[1:]),
#                             FinalBuyPrice=float(item[11].getText()),
#                             FinalBuyVolume=int(item[12].getText().replace(',','')),
#                             FinalSellPrice=float(item[13].getText()),
#                             FinalSellVolume=int(item[14].getText().replace(',',''))
#                         )
#                         stockRecord.save()
#                     except:
#                         print("Some data went wrong")

#         time.sleep(2)
#         start_date = start_date + delta

# @shared_task
# def crawl_tpex_stock_price_from_9208_to_9512():
#     url = "https://hist.tpex.org.tw/Hist/STOCK/AFTERTRADING/DAILY_CLOSE_QUOTES/RSTA3104_951218.HTML"
#     resp = requests.get(url)
#     resp.encoding = "big5"
#     soup = BeautifulSoup(resp.text, 'html.parser')
#     soup.find('table').find_all('tr')[0].getText()