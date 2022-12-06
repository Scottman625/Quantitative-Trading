from stockCore.models import Stock, AnnaulReport, FinancialReport
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
from celery import shared_task



def check_stocks_annual_reports():  
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':

            start_year = 2021
            end_year = 1998
            stock_code =  stock.stock_code

            while start_year >= end_year and str(start_year) not in stock.stockIPODate:
                year = start_year - 1911
                if AnnaulReport.objects.filter(stock_code=stock_code, year=year).count()==0:
                    crawl_stock_annaul_report.delay(stock_code, str(start_year-1911) )
                start_year = start_year - 1

def check_stocks_financial_reports():
    stocks = Stock.objects.all()
    
    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':

            start_year = 2021
            end_year = 1998
            stock_code = stock.stock_code

            while start_year >= end_year and str(start_year) not in stock.stockIPODate:
                year = start_year - 1911
                if FinancialReport.objects.filter(stock_code=stock_code, year=year).count()==0:
                    crawl_stock_annual_season_financial_report.delay(stock_code, str(start_year-1911) )
                start_year = start_year - 1

@shared_task
def crawl_stock_annaul_report(stock_code, tw_year):
    # url = 'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id=2337&year=110&mtype=F&'
    url = f'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id={stock_code}&year={tw_year}&mtype=F&'
    

    print(url)
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    try:
        if '查無所需資料' in resp.text:
            print('no data')
        else:
            print('has data')
            year = str(int(tw_year) + 1911)
            if AnnaulReport.objects.filter(stock_code=stock_code, year=year).count()==0:
                annaual_report = AnnaulReport()
                annaual_report.stock = Stock.objects.get(stock_code = stock_code)
                annaual_report.stock_code = stock_code
                annaual_report.year = year
                annaual_report.link = url
                annaual_report.save()
            else:
                print('already exist')
    except:
        print('crawl error!')

@shared_task
def crawl_stock_annual_season_financial_report(stock_code, tw_year):
    # url = f'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id={stock_code}&year={tw_year}&seamon=&mtype=A&'
    # url = 'https://doc.twse.com.tw/server-java/t57sb01?step=1&colorchg=1&co_id=2330&year=112&seamon=&mtype=A&'
    url = f'https://doc.twse.com.tw/server-java/t57sb01?check2858=Y&co_id={stock_code}&colorchg=1&year={tw_year}&step=1&seamon=&mtype=A&x=49&y=15'

    print(url)
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    try:
        if '查無所需資料' in resp.text:
            print('no data')
        else:
            print('has data')
            year = str(int(tw_year) + 1911)
            if FinancialReport.objects.filter(stock_code=stock_code, year=year).count()==0:
                financial_report = FinancialReport()
                financial_report.stock = Stock.objects.get(stock_code = stock_code)
                financial_report.stock_code = stock_code
                financial_report.year = year
                financial_report.link = url
                financial_report.save()
            else:
                print('already exist')
    except:
        print('crawl error!')