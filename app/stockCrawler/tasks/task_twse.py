from celery import shared_task
from stockCore.models import Stock, StockRecord, Index, Category
from datetime import datetime, date as thedate, timedelta
from bs4 import BeautifulSoup
import json
import requests
import time


@shared_task
def crawl_the_day_stock_price_and_index(date_string):

    #20210101
    the_date = datetime.strptime(date_string,"%Y%m%d")

    #start_date.strftime('%Y%m%d')
    url = f'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_string}&type=ALLBUT0999'
    print(url)

    # payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    # resp = requests.get('http://api.scraperapi.com', params=payload)

    resp = requests.get(url)
    info = json.loads(resp.text)
    
    # try:
    try:
        indexs = info['data1']

        for item in indexs:
            if (len(item) == 6 and "類" in item[0] or item[0] == '發行量加權股價指數'):
                if "電子類兩倍槓桿" not in item[0] and "電子類反向" not in item[0]:
                    # print(item[0]+item[1])
                    if(item[0]=='發行量加權股價指數'):
                        item[0] = '台股指數'
                    if(Index.objects.filter(name=item[0]).count() == 0):
                        index = Index(name=item[0])
                        index.save()
                    else:
                        index = Index.objects.get(name=item[0])
                    if IndexRecord.objects.filter(date=the_date,index=index).count() == 0:
                        try:
                            indexRecord = IndexRecord(
                                index=index,
                                date=the_date,
                                ClosingPrice=float(item[1].replace(',','')),
                                # Dir=BeautifulSoup(item[2]).find('p').text,
                                Dir=remove_html_tags(item[2]),
                                Change=float(item[3].replace(',','')),
                                Percent=float(item[4].replace(',','')),
                            )
                            indexRecord.save()
                        except:
                            print(item[0]+" Something wrong")
    except:
        print("no index data.")


    if info['fields8'] != None and len(info['fields8']) == 16:
        stocks = info['data8']
    else:
        stocks = info['data9']

    for item in stocks:
        if  len(item) == 16 and len(item[0]) == 4 :
            if(Stock.objects.filter(stock_code=item[0]).count() == 0):
                # print(item[1])
                stock = Stock(stock_code=item[0],name=item[1])
                stock.save()
            else:
                stock = Stock.objects.get(stock_code=item[0])

            if StockRecord.objects.filter(date=the_date,stock=stock).count() == 0:
                
                if item[12]=='':
                    finalBuyVolume = 0
                else:
                    finalBuyVolume = int(item[12].replace(',',''))

                if item[14]=='':
                    finalSellVolume = 0
                else:
                    finalSellVolume = int(item[14].replace(',',''))

                # if (stock.stock_code == '2330'):
                try:
                    stockRecord = StockRecord(
                        stock=stock,
                        date=the_date,
                        Volume=float(item[2].replace(',','')),
                        Transaction=int(item[3].replace(',','')),
                        TurnOver=float(item[4].replace(',','')),
                        OpeningPrice=float(item[5].replace(',','')),
                        DayHigh=float(item[6].replace(',','')),
                        DayLow=float(item[7].replace(',','')),
                        ClosingPrice=float(item[8].replace(',','')),
                        # Dir=BeautifulSoup(item[9]).find('p').text,
                        Dir=remove_html_tags(item[9]),
                        Change=float(item[10].replace(',','')),
                        FinalBuyPrice=float(item[11].replace(',','')),
                        FinalBuyVolume=finalBuyVolume,
                        FinalSellPrice=float(item[13].replace(',','')),
                        FinalSellVolume=finalSellVolume,
                    )
                    stockRecord.save()
                except:
                    print(item[1]+" Some data went wrong")
    # except:
    #     print("this date has no data")

def add_crawl_day_stock_price_before_20040211_task():
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '公司已下市':

            start_year = 2004
            end_year = 1999
            start_month_str = '0101'

            while start_year >= end_year:
                crawl_day_stock_price_by_stock_code_before_20040211.delay(stock.stock_code, f'{start_year}{start_month_str}')
                # crawl_day_stock_price_by_stock_code_before_20040211.delay(2330, f'{start_year}{start_month_str}')

                if start_month_str == '0101':
                    start_month_str = '1201'
                    start_year = start_year - 1
                elif start_month_str == '0201':
                    start_month_str = '0101'
                elif start_month_str == '0201':
                    start_month_str = '0101'
                elif start_month_str == '0301':
                    start_month_str = '0201'
                elif start_month_str == '0401':
                    start_month_str = '0301'
                elif start_month_str == '0501':
                    start_month_str = '0401'
                elif start_month_str == '0601':
                    start_month_str = '0501'
                elif start_month_str == '0701':
                    start_month_str = '0601'
                elif start_month_str == '0801':
                    start_month_str = '0701'
                elif start_month_str == '0901':
                    start_month_str = '0801'
                elif start_month_str == '1001':
                    start_month_str = '0901'
                elif start_month_str == '1101':
                    start_month_str = '1001'
                elif start_month_str == '1201':
                    start_month_str = '1101'

@shared_task
def crawl_day_stock_price_by_stock_code_before_20040211(stock_code, date_string):

    # url = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date=20130101&stockNo=2330&_=1644815557740'
    # url = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date=20130101&stockNo=2330'
    
    url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&date={date_string}&stockNo={stock_code}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    info = json.loads(resp.text)

    datas = info['data']
    length = len(datas)

    date = datas[length-2][0]
    ClosingPrice = datas[length-2][1]

    print(f'日期:{date}, 收盤價:{ClosingPrice}')

    year = str(int(date.split('/')[0])+1911)
    month = date.split('/')[1]
    day=date.split('/')[2]
    the_date = datetime.strptime(f'{year}{month}{day}',"%Y%m%d")

    stock = Stock.objects.get(stock_code=stock_code)

    if StockRecord.objects.filter(stock=stock, date=the_date).count() == 0:
        stockRecord = StockRecord(
            stock=stock,
            date=the_date,
            Volume=0,
            Transaction=0,
            TurnOver=0,
            OpeningPrice=ClosingPrice,
            DayHigh=ClosingPrice,
            DayLow=ClosingPrice,
            ClosingPrice=ClosingPrice,
            # Dir=BeautifulSoup(item[9]).find('p').text,
            Dir='',
            Change=0,
            FinalBuyPrice=0,
            FinalBuyVolume=0,
            FinalSellPrice=0,
            FinalSellVolume=0,
        )
        stockRecord.save()

def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def check_twse_stock_category():
    #date_string ex. 20210503
    the_date = datetime.strptime('20210531', '%Y%m%d')

    url = f'https://mops.twse.com.tw/nas/t21/sii/t21sc03_{str(the_date.year-1911)}_{str(the_date.month)}_0.html'
    print(url)
    # resp = requests.get("https://mops.twse.com.tw/nas/t21/sii/t21sc03_110_4_0.html")

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    # resp.encoding = 'big5' 
    # 測試結果是, 如果用 scraperapi 的話, 不要 encode, 就不會是亂碼~
    soup = BeautifulSoup(resp.text, 'html.parser')

    # day = calendar.monthrange(year+1911, month)[1]
    # date = datetime(year+1911, month, day)

    # try:

    totals = soup.find_all('table',{'border':'5'})
    for total in totals:
        total.find_all('tr')[-1].decompose()

    industry_tables = soup.find('table').find_all('table')
    industry_tables = industry_tables[0:-1:2]

    for industry_table in industry_tables:
        # 產業別
        category = industry_table.find_all('th',{'align':'left'})[0].string.replace('產業別：','')
        print(category)

        # print(category)
        if(Category.objects.filter(name=category).count() == 0):
            # print(item[1])
            theCategory = Category(name=category)
            theCategory.save()
        else:
            theCategory = Category.objects.filter(name=category)[0]
            while Category.objects.filter(name=category).count() > 1:
                Category.objects.filter(name=category)[1].delete()

        # print(industry_table.find_all('th',{'align':'right'})[0].string)
        array = industry_table.find_all('tr',{'align':'right'})
        for item in array:
            stock_code = item.find_all('td')[0].string.replace(' ','')
            stock = Stock.objects.get(stock_code=stock_code)
            if stock.category == None:
                stock.category = theCategory
                stock.save()
