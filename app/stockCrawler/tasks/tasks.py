from os import replace
from celery import shared_task
from requests.api import put
from stockCore.models import Stock, RevenueSheet, Category, DividendSheet, CashFlowStatement, IncomeStatement, BalanceSheet, StockRecord, KeyValueSheetSeason, KeyValueSheetCurrent, StockEvaluate, Index
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
import calendar
import time
import random
from requests.auth import HTTPProxyAuth



#done
@shared_task
def crawl_stock_info(stock_code):
    # stock_code = '2330'
    
    url = f'https://mops.twse.com.tw/mops/web/t05st03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&co_id={stock_code}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # print(soup.prettiefy())
    # try:
    info = soup.find(id="table01")

    if "公司不繼續公開發行" in info.text:
        stock = Stock.objects.get(stock_code=stock_code)
        stock.stockIndustry = "公司不繼續公開發行"
        stock.save()
    elif "公司不存在" in info.text:
        stock = Stock.objects.get(stock_code=stock_code)
        stock.stockIndustry = "此代號非公司"
        stock.save()
    elif "上市公司已下市" in info.text or '公司已下櫃' in info.text:
        stock = Stock.objects.get(stock_code=stock_code)
        stock.stockIndustry = "公司已下市"
        stock.save()
    else:
        tds = info.find_all('td')
        ths = info.find_all('th')
        l = len(tds)
        stockIPODate = None

        stockDividendFrequency = ''

        for index,item in enumerate(ths):
            if index > 0 and index < l-1:
                item_title = item.getText()
                # print(item_title)
                item_content = tds[index+1].getText().replace('\xa0','').replace(' ','')
                # print(item_content)
                if '產業類別' in item_title:
                    stockIndustry = item_content
                elif '公司名稱' in item_title and '公司名稱變更核准日期' not in item_title:
                    stockFullName = item_content
                elif '地址' in item_title:
                    stockAddress = item_content
                elif '董事長' in item_title:
                    stockChairman = item_content
                elif '總經理' in item_title:
                    stockManager = item_content
                elif '主要經營業務' in item_title:
                    stockMainBusiness = item_content
                elif '公司成立日期' in item_title:
                    stockCreatedDate = item_content
                elif '實收資本額' in item_title:
                    stockCapital = item_content
                elif '上市日期' in item_title:
                    if item_content != None:
                        stockIPODate = item_content
                        stockState = "上市"
                elif '上櫃日期' in item_title:
                    if stockIPODate == None and item_content != None:
                        stockIPODate = item_content
                        stockState = "上櫃"
                elif '普通股每股面額' in item_title:
                    stockCommonSharePrice = item_content
                elif '已發行普通股數或TDR原股發行股數' in item_title:
                    stockCommonShares = item_content
                elif '普通股盈餘分派或虧損撥補頻率' in item_title:
                    stockDividendFrequency = item_content
                elif '公司網址' in item_title:
                    stockCompanyURL = tds[index-1].getText().replace('\xa0','').replace(' ','')
        
        stock = Stock.objects.get(stock_code=stock_code)
        stock.stockIndustry = stockIndustry
        stock.stockFullName = stockFullName
        stock.stockAddress = stockAddress
        stock.stockChairman = stockChairman
        stock.stockManager = stockManager
        stock.stockMainBusiness = stockMainBusiness
        stock.stockCreatedDate = stockCreatedDate
        stock.stockCapital = stockCapital
        stock.stockIPODate = stockIPODate
        stock.stockState = stockState
        stock.stockCommonSharePrice = stockCommonSharePrice
        stock.stockCommonShares = stockCommonShares
        stock.stockDividendFrequency = stockDividendFrequency
        stock.stockCompanyURL = stockCompanyURL
        stock.save()
    # except:
    #     print('cannot get the stock info')

#done
@shared_task
def crawl_company_revenue(date_string):
    #date_string ex. 20210503
    the_date = datetime.strptime(date_string, '%Y%m%d')

    url = f'https://mops.twse.com.tw/nas/t21/sii/t21sc03_{str(the_date.year-1911)}_{str(the_date.month)}_0.html'
    print(url)
    # resp = requests.get("https://mops.twse.com.tw/nas/t21/sii/t21sc03_110_4_0.html")

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    # resp.encoding = 'big5'
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
        if category == '金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）':
            category = '金融保險業'
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
            if RevenueSheet.objects.filter(date=the_date,stock_code=stock_code).count() == 0:
                try:
                    stock = Stock.objects.get(stock_code=stock_code)
                    if stock.category == None:
                        stock.category = theCategory
                        stock.save()

                    sheet = RevenueSheet()
                    sheet.stock_code = stock_code
                    sheet.stock = stock
                    sheet.date = the_date
                    sheet.company_name = item.find_all('td')[1].string.replace(' ','')
                    sheet.this_month_revenue = int(item.find_all('td')[2].string.replace(' ','').replace(',',''))
                    sheet.last_month_revenue =  int(item.find_all('td')[3].string.replace(' ','').replace(',',''))
                    sheet.last_year_this_month_revenue = int(item.find_all('td')[4].string.replace(' ','').replace(',',''))
                    try:
                        sheet.percent_compare_last_month = float(item.find_all('td')[5].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_month > 1000:
                            sheet.percent_compare_last_month = 0
                    except:
                        sheet.percent_compare_last_month = 0
                    try:
                        sheet.percent_compare_last_year = float(item.find_all('td')[6].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_year > 1000:
                            sheet.percent_compare_last_year = 0
                    except:
                        sheet.percent_compare_last_year = 0
                    sheet.save()
                except:
                    print(item.find_all('td')[1].string+" Some data went wrong")
                    # print('公司代號'+item.find_all('td')[0].string)
                    # print('公司名稱'+item.find_all('td')[1].string)
                    # print('當月營收'+item.find_all('td')[2].string)
                    # print('上月營收'+item.find_all('td')[3].string)
                    # print('去年當月營收'+item.find_all('td')[4].string)
                    # print('上月比較增減(%)'+item.find_all('td')[5].string)
                    # print('去年同月增減(%)'+item.find_all('td')[6].string)
                    # print('當月累計營收'+item.find_all('td')[7].string)
                    # print('去年累計營收'+item.find_all('td')[8].string)
                    # print('前期比較增減(%)'+item.find_all('td')[9].string)
                    # print('備註'+item.find_all('td')[10].string)
    # except:
    #     print('cannot find data')

@shared_task
def crawl_tpex_company_revenue(date_string):
    the_date = datetime.strptime(date_string, '%Y%m%d')

    url = f'https://mops.twse.com.tw/nas/t21/otc/t21sc03_{str(the_date.year-1911)}_{str(the_date.month)}_0.html'
    print(url)
    # resp = requests.get("https://mops.twse.com.tw/nas/t21/sii/t21sc03_110_4_0.html")

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    # resp.encoding = 'big5'
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
        if category == '金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）':
            category = '金融保險業'
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
            if RevenueSheet.objects.filter(date=the_date,stock_code=stock_code).count() == 0:
                try:
                    stock = Stock.objects.get(stock_code=stock_code)
                    if stock.category == None:
                        stock.category = theCategory
                        stock.save()

                    sheet = RevenueSheet()
                    sheet.stock_code = stock_code
                    sheet.stock = stock
                    sheet.date = the_date
                    sheet.company_name = item.find_all('td')[1].string.replace(' ','')
                    sheet.this_month_revenue = int(item.find_all('td')[2].string.replace(' ','').replace(',',''))
                    sheet.last_month_revenue =  int(item.find_all('td')[3].string.replace(' ','').replace(',',''))
                    sheet.last_year_this_month_revenue = int(item.find_all('td')[4].string.replace(' ','').replace(',',''))
                    try:
                        sheet.percent_compare_last_month = float(item.find_all('td')[5].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_month > 1000:
                            sheet.percent_compare_last_month = 0
                    except:
                        sheet.percent_compare_last_month = 0
                    try:
                        sheet.percent_compare_last_year = float(item.find_all('td')[6].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_year > 1000:
                            sheet.percent_compare_last_year = 0
                    except:
                        sheet.percent_compare_last_year = 0
                    sheet.save()
                except:
                    print(item.find_all('td')[1].string+" Some data went wrong")


@shared_task
def crawl_foreign_company_revenue(date_string):
    the_date = datetime.strptime(date_string, '%Y%m%d')

    url = f'https://mops.twse.com.tw/nas/t21/sii/t21sc03_{str(the_date.year-1911)}_{str(the_date.month)}_1.html'
    print(url)
    # resp = requests.get("https://mops.twse.com.tw/nas/t21/sii/t21sc03_110_4_0.html")

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    # resp.encoding = 'big5'
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
        if category == '金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）':
            category = '金融保險業'
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
            if RevenueSheet.objects.filter(date=the_date,stock_code=stock_code).count() == 0:
                try:
                    stock = Stock.objects.get(stock_code=stock_code)
                    if stock.category == None:
                        stock.category = theCategory
                        stock.save()

                    sheet = RevenueSheet()
                    sheet.stock_code = stock_code
                    sheet.stock = stock
                    sheet.date = the_date
                    sheet.company_name = item.find_all('td')[1].string.replace(' ','')
                    sheet.this_month_revenue = int(item.find_all('td')[2].string.replace(' ','').replace(',',''))
                    sheet.last_month_revenue =  int(item.find_all('td')[3].string.replace(' ','').replace(',',''))
                    sheet.last_year_this_month_revenue = int(item.find_all('td')[4].string.replace(' ','').replace(',',''))
                    try:
                        sheet.percent_compare_last_month = float(item.find_all('td')[5].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_month > 1000:
                            sheet.percent_compare_last_month = 0
                    except:
                        sheet.percent_compare_last_month = 0
                    try:
                        sheet.percent_compare_last_year = float(item.find_all('td')[6].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_year > 1000:
                            sheet.percent_compare_last_year = 0
                    except:
                        sheet.percent_compare_last_year = 0
                    sheet.save()
                except:
                    print(item.find_all('td')[1].string+" Some data went wrong")

@shared_task
def crawl_foreign_tpex_company_revenue(date_string):
    the_date = datetime.strptime(date_string, '%Y%m%d')

    url = f'https://mops.twse.com.tw/nas/t21/otc/t21sc03_{str(the_date.year-1911)}_{str(the_date.month)}_1.html'
    print(url)
    # resp = requests.get("https://mops.twse.com.tw/nas/t21/sii/t21sc03_110_4_0.html")

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    # resp.encoding = 'big5'
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
        if category == '金融保險業（其中金控公司係控股公司，其申報之「營業收入」係認列所有子公司損益之合計數）':
            category = '金融保險業'
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
            if RevenueSheet.objects.filter(date=the_date,stock_code=stock_code).count() == 0:
                try:
                    stock = Stock.objects.get(stock_code=stock_code)
                    if stock.category == None:
                        stock.category = theCategory
                        stock.save()

                    sheet = RevenueSheet()
                    sheet.stock_code = stock_code
                    sheet.stock = stock
                    sheet.date = the_date
                    sheet.company_name = item.find_all('td')[1].string.replace(' ','')
                    sheet.this_month_revenue = int(item.find_all('td')[2].string.replace(' ','').replace(',',''))
                    sheet.last_month_revenue =  int(item.find_all('td')[3].string.replace(' ','').replace(',',''))
                    sheet.last_year_this_month_revenue = int(item.find_all('td')[4].string.replace(' ','').replace(',',''))
                    try:
                        sheet.percent_compare_last_month = float(item.find_all('td')[5].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_month > 1000:
                            sheet.percent_compare_last_month = 0
                    except:
                        sheet.percent_compare_last_month = 0
                    try:
                        sheet.percent_compare_last_year = float(item.find_all('td')[6].string.replace(' ','').replace(',',''))
                        if sheet.percent_compare_last_year > 1000:
                            sheet.percent_compare_last_year = 0
                    except:
                        sheet.percent_compare_last_year = 0
                    sheet.save()
                except:
                    print(item.find_all('td')[1].string+" Some data went wrong")

#done
@shared_task
def crawl_company_balance_sheet(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '01'
    elif startDate.month == 6:
        season = '02'
    elif startDate.month == 9:
        season = '03'
    elif startDate.month == 12:
        season = '04'

    url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)
    
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)
    # resp = requests.get(url)

    # s = requests.Session()
    # s.proxies = {"http": 'https://196.18.237.212:8000' , "https": 'https://196.18.237.212:8000'}
    # s.auth = HTTPProxyAuth('nwm6KJ', '0fyNLL')
    # s.trust_env=False

    # proxy={
    #     'http':'196.18.237.212:8000',
    #     'https':'196.18.237.212:8000'
    # }

    # resp = requests.get(url, proxies=proxy, verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # try:
    table = soup.find('table',{'class':'hasBorder'})
    trs = table.find_all('tr')

    currentAssets_Cash = 0
    currentAssets_FinancialSubTotal = 0
    currentAssets_AccountReceivableSubTotal = 0
    currentAssets_Others = 0
    currentAssets_Inventory = 0

    nonCurrentAssets_FinancialSubTotoal = 0
    nonCurrentAssets_RealEstate = 0
    nonCurrentAssets_Others = 0
    nonCurrentAssets_Total = 0

    assetTotal = 0

    currentDebt_Cash = 0
    currentDebt_FinancialSubTotal = 0
    currentDebt_AccountReceivableSubTotal = 0
    currentDebt_Others = 0
    currentDebt_Total = 0
    
    nonCurrentDebt_LongTermLoan = 0
    nonCurrentDebt_Lease = 0
    nonCurrentDebt_CompanyBond = 0
    nonCurrentDebt_Others = 0
    nonCurrentDebt_Total = 0

    debtTotal = 0

    equity_CommonStock = 0 
    equity_CapitalReserve = 0
    equity_RetainedEarnings = 0
    equity_Others = 0
    equity_NonControllingInterests = 0
    equity_Total = 0

    for item in trs:
        try:
            item_title = item.find_all('td')[0].getText().replace(' ','')
            item_title = ''.join(item_title.split())
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '現金及約當現金' in item_title:
                # print(item_title)
                currentAssets_Cash = item_content
            elif ('透過損益按公允價值衡量之金融資產－流動' in item_title) or ('透過其他綜合損益按公允價值衡量之金融資產－流動' in item_title) or ('按攤銷後成本衡量之金融資產－流動' in item_title) or ('避險之金融資產－流動' in item_title):
                # print(item_title)
                currentAssets_FinancialSubTotal =  currentAssets_FinancialSubTotal + int(item_content)
            elif ('應收帳款淨額' in item_title)  or ('應收帳款－關係人淨額' in item_title) or ('其他應收款－關係人淨額' in item_title):
                # print(item_title)
                currentAssets_AccountReceivableSubTotal =  currentAssets_AccountReceivableSubTotal + int(item_content)
            elif '存貨' in item_title:
                # print(item_title)
                currentAssets_Inventory =  item_content
            elif '其他流動資產' in item_title:
                # print(item_title)
                currentAssets_Others =  item_content
            elif '非流動資產合計' in item_title:
                # print(item_title)
                nonCurrentAssets_Total =  item_content
            elif '流動資產合計' in item_title:
                # print(item_title)
                currentAssets_Total =  item_content
            elif ('透過其他綜合損益按公允價值衡量之金融資產－非流動' in item_title) or ('按攤銷後成本衡量之金融資產－非流動' in item_title) or ('採用權益法之投資' in item_title):
                # print(item_title)
                nonCurrentAssets_FinancialSubTotoal =  nonCurrentAssets_FinancialSubTotoal + int(item_content)
            elif '不動產、廠房及設備' in item_title:
                # print(item_title)
                nonCurrentAssets_RealEstate = item_content
            elif '其他非流動資產' in item_title:
                # print(item_title)
                nonCurrentAssets_Others =  item_content
            elif '資產總額' in item_title or '資產總計' in item_title:
                # print(item_title)
                assetTotal =  item_content
            elif '短期借款' in item_title:
                # print(item_title)
                currentDebt_Cash =  item_content
            elif '應付短期票券' in item_title or '透過損益按公允價值衡量之金融負債－流動' in item_title or '避險之金融負債－流動' in item_title:
                # print(item_title)
                currentDebt_FinancialSubTotal =  currentDebt_FinancialSubTotal + int(item_content)
            elif '應付帳款' in item_title or '應付帳款－關係人' in item_title or '其他應付款' in item_title:
                # print(item_title)
                currentDebt_AccountReceivableSubTotal =  currentDebt_AccountReceivableSubTotal + int(item_content)
            elif '其他流動負債' in item_title:
                # print(item_title)
                currentDebt_Others =  item_content
            elif '非流動負債合計' in item_title:
                # print(item_title + item_content)
                nonCurrentDebt_Total =  item_content
            elif '流動負債合計' in item_title:
                # print(item_title)
                currentDebt_Total =  item_content
            elif '應付公司債' in item_title:
                # print(item_title)
                nonCurrentDebt_CompanyBond =  item_content
            elif '長期借款' in item_title:
                # print(item_title)
                nonCurrentDebt_LongTermLoan =  item_content
            elif '租賃負債－非流動' in item_title:
                # print(item_title)
                nonCurrentDebt_Lease =  item_content
            elif '其他非流動負債' in item_title:
                # print(item_title)
                nonCurrentDebt_Others =  item_content
            elif '負債總額' in item_title or '負債總計' in item_title:
                # print(item_title)
                debtTotal =  item_content
            elif '股本合計' in item_title:
                # print(item_title)
                equity_CommonStock =  item_content
                print(equity_CommonStock)
            elif '資本公積合計' in item_title:
                # print(item_title)
                equity_CapitalReserve =  item_content
            elif '保留盈餘合計' in item_title:
                # print(item_title)
                equity_RetainedEarnings =  item_content
            elif '其他權益合計' in item_title:
                # print(item_title)
                equity_Others =  item_content
            elif '非控制權益' in item_title:
                # print(item_title)
                equity_NonControllingInterests =  item_content
            elif '權益總額' in item_title:
                # print(item_title)
                equity_Total =  item_content
                # print(equity_Total)
        except:
            print('this tr no content')

    print("股本 " + equity_CommonStock)
    print("資產 " + assetTotal)
    equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
    # print("每股淨值 " + equity_Per_Share)

    stock = Stock.objects.filter(stock_code=stock_code)[0]

    if BalanceSheet.objects.filter(stock=stock, date=startDate).count() == 0:
        sheet = BalanceSheet()
    else:
        sheet = BalanceSheet.objects.get(stock=stock, date=startDate)

    sheet.stock_code = stock_code
    sheet.stock = stock
    sheet.date = startDate

    sheet.CurrentAssets_Cash = currentAssets_Cash
    sheet.CurrentAssets_FinancialSubTotal = currentAssets_FinancialSubTotal
    sheet.CurrentAssets_AccountReceivableSubTotal = currentAssets_AccountReceivableSubTotal
    sheet.CurrentAssets_Inventory = currentAssets_Inventory
    sheet.CurrentAssets_Others = currentAssets_Others
    sheet.CurrentAssets_Total = currentAssets_Total

    sheet.NonCurrentAssets_FinancialSubTotoal = nonCurrentAssets_FinancialSubTotoal
    sheet.NonCurrentAssets_RealEstate = nonCurrentAssets_RealEstate
    sheet.NonCurrentAssets_Others = nonCurrentAssets_Others
    sheet.NonCurrentAssets_Total = nonCurrentAssets_Total

    sheet.AssetsTotal = assetTotal

    sheet.CurrentDebt_Cash = currentDebt_Cash
    sheet.CurrentDebt_FinancialSubTotal = currentDebt_FinancialSubTotal
    sheet.CurrentDebt_AccountReceivableSubTotal = currentDebt_AccountReceivableSubTotal
    sheet.CurrentDebt_Others = currentDebt_Others
    sheet.CurrentDebt_Total = currentDebt_Total

    sheet.NonCurrentDebt_CompanyBond = nonCurrentDebt_CompanyBond
    sheet.NonCurrentDebt_Lease = nonCurrentDebt_Lease
    sheet.NonCurrentDebt_LongTermLoan = nonCurrentDebt_LongTermLoan
    sheet.NonCurrentDebt_Others = nonCurrentDebt_Others
    sheet.NonCurrentDebt_Total = nonCurrentDebt_Total

    sheet.DebtTotal = debtTotal

    sheet.Equity_CommonStock = equity_CommonStock
    sheet.Equity_CapitalReserve = equity_CapitalReserve
    sheet.Equity_RetainedEarnings = equity_RetainedEarnings
    sheet.Equity_Others = equity_Others
    sheet.Equity_NonControllingInterests = equity_NonControllingInterests
    sheet.Equity_Total = equity_Total
    sheet.Equity_Per_Share = equity_Per_Share

    sheet.save()

    crawl_stock_share_holder(stock.stock_code, date_string)

    # except:
    #     print('no data!')

    # time.sleep(random.randint(5,10))

@shared_task
def crawl_company_balance_sheet_ajax(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '01'
    elif startDate.month == 6:
        season = '02'
    elif startDate.month == 9:
        season = '03'
    elif startDate.month == 12:
        season = '04'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb03'
    print(url)
    
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.post('http://api.scraperapi.com', params=payload, data={'encodeURIComponent':'1', 'TYPEK':'sii', 'step':'2', 'year':f'{year}', 'season':f'{season}', 'co_id':stock_code, 'firstin':'1'})

    soup = BeautifulSoup(resp.text, 'html.parser')

    # try:
    table = soup.find('table',{'class':'hasBorder'})
    trs = table.find_all('tr')

    currentAssets_Cash = 0
    currentAssets_FinancialSubTotal = 0
    currentAssets_AccountReceivableSubTotal = 0
    currentAssets_Others = 0
    currentAssets_Inventory = 0
    currentDebt_Total = 0

    nonCurrentAssets_FinancialSubTotoal = 0
    nonCurrentAssets_RealEstate = 0
    nonCurrentAssets_Others = 0
    nonCurrentAssets_Total = 0

    assetTotal = 0

    currentDebt_Cash = 0
    currentDebt_FinancialSubTotal = 0
    currentDebt_AccountReceivableSubTotal = 0
    currentDebt_Others = 0
    
    nonCurrentDebt_LongTermLoan = 0
    nonCurrentDebt_Lease = 0
    nonCurrentDebt_CompanyBond = 0
    nonCurrentDebt_Others = 0
    nonCurrentDebt_Total = 0

    debtTotal = 0

    equity_CommonStock = 0 
    equity_CapitalReserve = 0
    equity_RetainedEarnings = 0
    equity_Others = 0
    equity_NonControllingInterests = 0
    equity_Total = 0

    for item in trs:
        try:
            item_title = item.find_all('td')[0].getText().replace(' ','')
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '現金及約當現金' in item_title:
                # print(item_title)
                currentAssets_Cash = item_content
            elif ('透過損益按公允價值衡量之金融資產－流動' in item_title) or ('透過其他綜合損益按公允價值衡量之金融資產－流動' in item_title) or ('按攤銷後成本衡量之金融資產－流動' in item_title) or ('避險之金融資產－流動' in item_title):
                # print(item_title)
                currentAssets_FinancialSubTotal =  currentAssets_FinancialSubTotal + int(item_content)
            elif ('應收帳款淨額' in item_title)  or ('應收帳款－關係人淨額' in item_title) or ('其他應收款－關係人淨額' in item_title):
                # print(item_title)
                currentAssets_AccountReceivableSubTotal =  currentAssets_AccountReceivableSubTotal + int(item_content)
            elif '存貨' in item_title:
                # print(item_title)
                currentAssets_Inventory =  item_content
            elif '其他流動資產' in item_title:
                # print(item_title)
                currentAssets_Others =  item_content
            elif '非流動資產合計' in item_title:
                # print(item_title)
                nonCurrentAssets_Total =  item_content
            elif '流動資產合計' in item_title:
                # print(item_title)
                currentAssets_Total =  item_content
            elif ('透過其他綜合損益按公允價值衡量之金融資產－非流動' in item_title) or ('按攤銷後成本衡量之金融資產－非流動' in item_title) or ('採用權益法之投資' in item_title):
                # print(item_title)
                nonCurrentAssets_FinancialSubTotoal =  nonCurrentAssets_FinancialSubTotoal + int(item_content)
            elif '不動產、廠房及設備' in item_title:
                # print(item_title)
                nonCurrentAssets_RealEstate = item_content
            elif '其他非流動資產' in item_title:
                # print(item_title)
                nonCurrentAssets_Others =  item_content
            elif '資產總額' in item_title or '資產總計' in item_title:
                # print(item_title)
                assetTotal =  item_content
            elif '短期借款' in item_title:
                # print(item_title)
                currentDebt_Cash =  item_content
            elif '應付短期票券' in item_title or '透過損益按公允價值衡量之金融負債－流動' in item_title or '避險之金融負債－流動' in item_title:
                # print(item_title)
                currentDebt_FinancialSubTotal =  currentDebt_FinancialSubTotal + int(item_content)
            elif '應付帳款' in item_title or '應付帳款－關係人' in item_title or '其他應付款' in item_title:
                # print(item_title)
                currentDebt_AccountReceivableSubTotal =  currentDebt_AccountReceivableSubTotal + int(item_content)
            elif '其他流動負債' in item_title:
                # print(item_title)
                currentDebt_Others =  item_content
            elif '非流動負債合計' in item_title:
                # print(item_title + item_content)
                nonCurrentDebt_Total =  item_content
            elif '流動負債合計' in item_title:
                # print(item_title)
                currentDebt_Total =  item_content
            elif '應付公司債' in item_title:
                # print(item_title)
                nonCurrentDebt_CompanyBond =  item_content
            elif '長期借款' in item_title:
                # print(item_title)
                nonCurrentDebt_LongTermLoan =  item_content
            elif '租賃負債－非流動' in item_title:
                # print(item_title)
                nonCurrentDebt_Lease =  item_content
            elif '其他非流動負債' in item_title:
                # print(item_title)
                nonCurrentDebt_Others =  item_content
            elif '負債總額' in item_title or '負債總計' in item_title:
                # print(item_title)
                debtTotal =  item_content
            elif '股本合計' in item_title or item_title == '股本':
                # print(item_title)
                equity_CommonStock =  item_content
            elif '資本公積合計' in item_title:
                # print(item_title)
                equity_CapitalReserve =  item_content
            elif '保留盈餘合計' in item_title:
                # print(item_title)
                equity_RetainedEarnings =  item_content
            elif '其他權益合計' in item_title:
                # print(item_title)
                equity_Others =  item_content
            elif '非控制權益' in item_title:
                # print(item_title)
                equity_NonControllingInterests =  item_content
            elif '權益總額' in item_title or '權益總計' in item_title:
                # print(item_title)
                equity_Total =  item_content
                # print(equity_Total)
        except:
            print('this tr no content')

    equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
    
    stock = Stock.objects.filter(stock_code=stock_code)[0]

    if BalanceSheet.objects.filter(stock=stock, date=startDate).count() == 0:
        sheet = BalanceSheet()
    else:
        sheet = BalanceSheet.objects.get(stock=stock, date=startDate)

    sheet.stock_code = stock_code
    sheet.stock = stock
    sheet.date = startDate

    sheet.CurrentAssets_Cash = currentAssets_Cash
    sheet.CurrentAssets_FinancialSubTotal = currentAssets_FinancialSubTotal
    sheet.CurrentAssets_AccountReceivableSubTotal = currentAssets_AccountReceivableSubTotal
    sheet.CurrentAssets_Inventory = currentAssets_Inventory
    sheet.CurrentAssets_Others = currentAssets_Others
    sheet.CurrentAssets_Total = currentAssets_Total

    sheet.NonCurrentAssets_FinancialSubTotoal = nonCurrentAssets_FinancialSubTotoal
    sheet.NonCurrentAssets_RealEstate = nonCurrentAssets_RealEstate
    sheet.NonCurrentAssets_Others = nonCurrentAssets_Others
    sheet.NonCurrentAssets_Total = nonCurrentAssets_Total

    sheet.AssetsTotal = assetTotal

    sheet.CurrentDebt_Cash = currentDebt_Cash
    sheet.CurrentDebt_FinancialSubTotal = currentDebt_FinancialSubTotal
    sheet.CurrentDebt_AccountReceivableSubTotal = currentDebt_AccountReceivableSubTotal
    sheet.CurrentDebt_Others = currentDebt_Others
    sheet.CurrentDebt_Total = currentDebt_Total

    sheet.NonCurrentDebt_CompanyBond = nonCurrentDebt_CompanyBond
    sheet.NonCurrentDebt_Lease = nonCurrentDebt_Lease
    sheet.NonCurrentDebt_LongTermLoan = nonCurrentDebt_LongTermLoan
    sheet.NonCurrentDebt_Others = nonCurrentDebt_Others
    sheet.NonCurrentDebt_Total = nonCurrentDebt_Total

    sheet.DebtTotal = debtTotal

    sheet.Equity_CommonStock = equity_CommonStock
    sheet.Equity_CapitalReserve = equity_CapitalReserve
    sheet.Equity_RetainedEarnings = equity_RetainedEarnings
    sheet.Equity_Others = equity_Others
    sheet.Equity_NonControllingInterests = equity_NonControllingInterests
    sheet.Equity_Total = equity_Total
    sheet.Equity_Per_Share = equity_Per_Share

    sheet.save()

#done, this function must go after crawl balance sheet
@shared_task
def crawl_stock_share_holder(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)

    year = startDate.year - 1911
    month = startDate.month

    url = f'https://mops.twse.com.tw/mops/web/ajax_stapap1?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={year}&month={month}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)
    # resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    try:
        tables = soup.find_all('table',{'class':'noBorder'})
        for item in tables:
            if '全體董監持股合計' in item.text:
                table = item
        tds = table.find_all('td')
        l = len(tds)

        for index,item in enumerate(tds):
            if index > 0 and index < l-1:
                item_title = item.getText()
                item_content = tds[index+1].getText().replace('\xa0','').replace(' ','').replace(',','')
                if '全體董監持股合計' in item_title:
                    directorSupervisorShares = item_content
                    print(item_title +  item_content)
                elif '全體董監持股設質合計' in item_title:
                    directorSupervisorPledgeShares = item_content
                    print(item_title +  item_content)

        sheet = BalanceSheet.objects.get(stock=stock,date=startDate)
        sheet.DirectorSupervisorShares = directorSupervisorShares
        sheet.DirectorSupervisorPledgeShares = directorSupervisorPledgeShares
        sheet.save()
    except:
        print("load error!")

    time.sleep(random.randint(2,10))

#done
@shared_task
def crawl_company_income_sheet(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)
    year = startDate.year - 1911
    print(stock_code,type(stock_code))
    if startDate.month == 3:
        season = '01'
    elif startDate.month == 6:
        season = '02'
    elif startDate.month == 9:
        season = '03'
    elif startDate.month == 12:
        season = '04'
    if stock_code == 5871 or stock_code == '5871':
        url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=2&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
        print(url)
    else:
        url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
        print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    
    resp = requests.get('http://api.scraperapi.com', params=payload)
    

    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table',{'class':'hasBorder'})
    trs = table.find_all('tr')
    ths = table.find_all('th')
    PeriodTitle = ths[3].getText()
    print(PeriodTitle)
    last_item = ''
    for item in ths:
        if '會計項目' in last_item:
            PeriodTitle = item.getText()
            print('item')
            break
        last_item  = item
    revenue = 0
    cost = 0
    gross = 0
    Gross_Net = 0
    promotionExpense = 0
    manageExpense = 0
    researchExpense = 0
    totalExpense = 0

    operatingProfit = 0
    profitBeforeTax = 0
    OtherIncomeExpensesNet = 0
    OtherIncome = 0
    OtherExpenses = 0
    OutOperatingInterestIncome = 0
    OutOperatingOtherIncome = 0
    OutOperatingLossNet = 0
    OutOperatingFinancialcosts = 0
    OutOperatingAffiliateNet = 0
    OutOperatingProfit = 0
    TotalIncomeTaxExpense = 0
    ProfitAfterTax = 0

    ProfitAfterTax = 0
    PeriodProfit = 0
    EquityInstrumentUnrealizedProfit = 0
    HedgingInstrumentProfit = 0
    ComprehensiveAffiliateIncome = 0
    ComprehensiveIncomeTax = 0
    ComprehensiveItem = 0
    ForeignFinancialExchangeDifferences = 0
    DebtInstrumentUnrealizedProfit = 0
    ComprehensiveHedgingInstrumentProfit = 0
    ReclassifiedAffiliateIncome  = 0
    ReclassifiedIncomeTax = 0
    FollowingReclassifiedItem = 0
    ComprehensiveTotalProfit = 0
    OtherComprehensivePartIncomeTax = 0
    CashFlowHedging = 0
    ForeignNetInvestmentHedging = 0

    otherIncome = 0
    totalIncome = 0
    ParentProfit = 0
    ChildProfit = 0
    ParentComprehensiveProfit = 0
    ChildComprehensiveProfit = 0
    ePS_Period = 0
    DilutionEPSPeriod = 0

    Net_Sales = 0
    SalesProfit = 0
    UnrealizedSalesProfit = 0
    UnsaleFinancialAssetsUnrealizedProfit = 0
    RemeasurementOfDefinedBenefitPlans = 0
    CashFlowHedgingInstrumentsProfits = 0

    CostOfGoodsSold = 0
    EPSBasicIncomefromContinuingOperation = 0
    EPSDilutionIncomefromContinuingOperation = 0

    SalesRevenue = 0
    SalesReturn = 0
    SalesDiscount = 0
    ExpectedCreditImpairmentLosses = 0
    ComprehensiveOtherItem = 0

    InvestmentIncome = 0
    RentalIncome = 0
    OtherOperatingIncomeNet = 0
    InterestExpense = 0
    InvestmentSpending = 0
    RentalCost = 0
    OtherOperatingCosts = 0


    last_item_title = ''
    for item in trs:
        try:
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            
            if '營業收入合計' in item_title and item_content != '':
                revenue = item_content
            elif ('採用權益法認列之關聯企業及合資之其他綜合損益之份額-可能重分類至損益之項目' in item_title or '採用權益法認列關聯企業及合資之其他綜合損益之份額-可能重分類至損益之項目' in item_title) and item_content != '':
                ReclassifiedAffiliateIncome =  item_content
            elif '營業毛利（毛損）淨額' in item_title and item_content != '':
                Gross_Net =  item_content
            elif '營業成本合計' in item_title and item_content != '':
                cost =  item_content
            elif '營業毛利（毛損）' in item_title and item_content != '':
                gross =  item_content
            elif '推銷費用' in item_title and item_content != '':
                promotionExpense =  item_content
            elif '管理費用' in item_title and item_content != '':
                manageExpense =  item_content
            elif '研究發展費用' in item_title and item_content != '':
                researchExpense =  item_content
            elif '營業費用合計' in item_title and item_content != '':
                totalExpense =  item_content
            elif '其他收益及費損淨額' in item_title and item_content != '':
                OtherIncomeExpensesNet =  item_content
            elif '其他收益' in item_title and item_content != '':
                OtherIncome =  item_content
            elif '其他費損' in item_title and item_content != '':
                OtherExpenses =  item_content
            elif '營業利益（損失）' in item_title and item_content != '':
                operatingProfit =  item_content
            elif '利息收入' in item_title and item_content != '':
                OutOperatingInterestIncome =  item_content
            elif '其他收入' in item_title and item_content != '':
                OutOperatingOtherIncome =  item_content
            elif '其他利益及損失淨額' in item_title and item_content != '':
                OutOperatingLossNet =  item_content
            elif '財務成本淨額' in item_title and item_content != '':
                OutOperatingFinancialcosts =  item_content
            elif '採用權益法認列之關聯企業及合資損益之份額淨額' in item_title and item_content != '':
                OutOperatingAffiliateNet =  item_content
            elif '營業外收入及支出合計' in item_title and item_content != '':
                OutOperatingProfit =  item_content
            elif '稅前淨利（淨損）' in item_title and item_content != '':
                profitBeforeTax =  item_content
            elif '所得稅費用（利益）合計' in item_title and item_content != '':
                TotalIncomeTaxExpense =  item_content
            elif '繼續營業單位本期淨利（淨損）' in item_title and item_content != '':
                ProfitAfterTax =  item_content
            elif '本期淨利' in item_title and item_content != '':
                PeriodProfit =  item_content
            elif '透過其他綜合損益按公允價值衡量之權益工具投資未實現評價損益' in item_title and item_content != '':
                EquityInstrumentUnrealizedProfit =  item_content
            elif '避險工具之損益－不重分類至損益' in item_title and item_content != '':
                HedgingInstrumentProfit =  item_content
            elif '採用權益法認列之關聯企業及合資之其他綜合損益之份額-不重分類至損益之項目' in item_title and item_content != '':
                ComprehensiveAffiliateIncome =  item_content
            elif '與不重分類之項目相關之所得稅' in item_title and item_content != '':
                ComprehensiveIncomeTax =  item_content
            elif '不重分類至損益之項目' in item_title and item_content != '':
                ComprehensiveItem =  item_content
            elif '國外營運機構財務報表換算之兌換差額' in item_title and item_content != '':
                ForeignFinancialExchangeDifferences =  item_content
            elif '透過其他綜合損益按公允價值衡量之債務工具投資未實現評價損益' in item_title and item_content != '':
                DebtInstrumentUnrealizedProfit =  item_content
            elif '避險工具之損益' in item_title and item_content != '':
                ComprehensiveHedgingInstrumentProfit =  item_content
            elif '與可能重分類之項目相關之所得稅' in item_title and item_content != '':
                ReclassifiedIncomeTax =  item_content
            elif '後續可能重分類至損益之項目' in item_title and item_content != '':
                FollowingReclassifiedItem =  item_content
            elif '採用權益法認列之關聯企業及合資之其他綜合損益之份額合計' in item_title and item_content != '':
                ComprehensiveTotalProfit =  item_content
            elif '與其他綜合損益組成部分相關之所得稅' in item_title and item_content != '':
                OtherComprehensivePartIncomeTax =  item_content
            elif '現金流量避險' in item_title and item_content != '':
                CashFlowHedging =  item_content
            elif '國外營運機構淨投資避險' in item_title and item_content != '':
                ForeignNetInvestmentHedging =  item_content
            elif '其他綜合損益（淨額）' in item_title and item_content != '':
                otherIncome =  item_content
            elif '本期綜合損益總額' in item_title and item_content != '':
                totalIncome =  item_content
            elif ('母公司業主（淨利∕損）' in item_title or '母公司業主（淨利／損）' in item_title) and item_content != '':
                ParentProfit =  item_content
            elif ('非控制權益（淨利∕損）' in item_title or '非控制權益（淨利／損）' in item_title) and item_content != '':
                ChildProfit =  item_content
            elif '母公司業主（綜合損益）' in item_title and item_content != '':
                ParentComprehensiveProfit =  item_content
            elif '非控制權益（綜合損益）' in item_title and item_content != '':
                ChildComprehensiveProfit =  item_content
            elif '基本每股盈餘' in item_title and item_content != '':
                ePS_Period =  item_content
            elif '稀釋每股盈餘' in item_title and item_content != '':
                DilutionEPSPeriod =  item_content
            elif '銷貨收入淨額' in item_title and item_content != '':
                Net_Sales =  item_content
            elif '已實現銷貨（損）益' in item_title and item_content != '':
                SalesProfit =  item_content
            elif '未實現銷貨（損）益' in item_title and item_content != '':
                UnrealizedSalesProfit = item_content
            elif '備供出售金融資產未實現評價損益' in item_title and item_content != '':
                UnsaleFinancialAssetsUnrealizedProfit =  item_content
            elif '確定福利計畫之再衡量數' in item_title and item_content != '':
                RemeasurementOfDefinedBenefitPlans =  item_content
            elif '現金流量避險中屬有效避險部分之避險工具利益(損失)' in item_title and item_content != '':
                CashFlowHedgingInstrumentsProfits =  item_content
                print('CashFlowHedgingInstrumentsProfits:',CashFlowHedgingInstrumentsProfits)
            elif '銷貨成本' in item_title and item_content != '':
                CostOfGoodsSold =  item_content
            elif '繼續營業單位淨利（淨損）' in item_title and item_content != '' and last_item_title == '基本每股盈餘':
                EPSBasicIncomefromContinuingOperation = item_content
            elif '繼續營業單位淨利（淨損）' in item_title and item_content != '' and last_item_title == '稀釋每股盈餘':
                EPSDilutionIncomefromContinuingOperation =  item_content
            elif '銷貨收入' in item_title and item_content != '':
                SalesRevenue = item_content
            elif '銷貨退回' in item_title and item_content != '':
                SalesReturn =  item_content
            elif '銷貨折讓' in item_title and item_content != '':
                SalesDiscount =  item_content
            elif '預期信用減損損失（利益）' in item_title and item_content != '':
                ExpectedCreditImpairmentLosses =  item_content
            elif '不重分類至損益之其他項目' in item_title and item_content != '':
                ComprehensiveOtherItem =  item_content
            elif '投資收入' in item_title and item_content != '':
                InvestmentIncome = item_content
            elif '租賃收入' in item_title and item_content != '':
                RentalIncome =  item_content
            elif '其他營業收入淨額' in item_title and item_content != '':
                OtherOperatingIncomeNet =  item_content
            elif '利息費用' in item_title and item_content != '':
                InterestExpense =  item_content
            elif '投資支出' in item_title and item_content != '':
                InvestmentSpending =  item_content
            elif '租賃成本' in item_title and item_content != '':
                RentalCost =  item_content
            elif '其他營業成本' in item_title and item_content != '':
                OtherOperatingCosts =  item_content
            last_item_title = item_title
        except:
            print('this tr no content')

    if IncomeStatement.objects.filter(stock=stock, date=startDate).count() == 0:
        stateMent = IncomeStatement()
    else:
        stateMent = IncomeStatement.objects.get(stock=stock, date=startDate)

    stateMent.stock_code = stock_code
    stateMent.stock = stock
    stateMent.date = startDate
    stateMent.PeriodTitle = PeriodTitle
    stateMent.Revenue = revenue
    stateMent.Cost = cost
    stateMent.Gross = gross
    stateMent.Gross_Net = Gross_Net
    stateMent.PromotionExpense = promotionExpense
    stateMent.ManageExpense = manageExpense
    stateMent.ResearchExpense = researchExpense
    stateMent.TotalExpense = totalExpense
    stateMent.OtherIncomeExpensesNet = OtherIncomeExpensesNet
    stateMent.OtherIncome = OtherIncome
    stateMent.OtherExpenses = OtherExpenses
    stateMent.OperatingProfit = operatingProfit
    stateMent.OutOperatingInterestIncome = OutOperatingInterestIncome
    stateMent.OutOperatingOtherIncome = OutOperatingOtherIncome
    stateMent.OutOperatingLossNet = OutOperatingLossNet
    stateMent.OutOperatingFinancialcosts = OutOperatingFinancialcosts
    stateMent.OutOperatingAffiliateNet = OutOperatingAffiliateNet
    stateMent.OutOperatingProfit = OutOperatingProfit
    stateMent.ProfitBeforeTax = profitBeforeTax
    stateMent.TotalIncomeTaxExpense = TotalIncomeTaxExpense
    stateMent.ProfitAfterTax = ProfitAfterTax
    stateMent.PeriodProfit = PeriodProfit
    stateMent.EquityInstrumentUnrealizedProfit = EquityInstrumentUnrealizedProfit
    stateMent.HedgingInstrumentProfit = HedgingInstrumentProfit
    stateMent.ComprehensiveAffiliateIncome = ComprehensiveAffiliateIncome
    stateMent.ComprehensiveIncomeTax = ComprehensiveIncomeTax
    stateMent.ComprehensiveItem = ComprehensiveItem
    stateMent.ForeignFinancialExchangeDifferences = ForeignFinancialExchangeDifferences
    stateMent.DebtInstrumentUnrealizedProfit = DebtInstrumentUnrealizedProfit
    stateMent.ComprehensiveHedgingInstrumentProfit = ComprehensiveHedgingInstrumentProfit
    stateMent.ReclassifiedAffiliateIncome = ReclassifiedAffiliateIncome
    stateMent.ReclassifiedIncomeTax = ReclassifiedIncomeTax
    stateMent.FollowingReclassifiedItem = FollowingReclassifiedItem
    stateMent.ComprehensiveTotalProfit = ComprehensiveTotalProfit
    stateMent.OtherComprehensivePartIncomeTax = OtherComprehensivePartIncomeTax
    stateMent.CashFlowHedging = CashFlowHedging
    stateMent.ForeignNetInvestmentHedging = ForeignNetInvestmentHedging
    stateMent.OtherIncome = otherIncome
    stateMent.TotalIncome = totalIncome
    stateMent.ParentProfit = ParentProfit
    stateMent.TotalIncome = totalIncome
    stateMent.ChildProfit = ChildProfit
    stateMent.ParentComprehensiveProfit = ParentComprehensiveProfit
    stateMent.ChildComprehensiveProfit = ChildComprehensiveProfit
    stateMent.EPSPeriod = ePS_Period
    stateMent.DilutionEPSPeriod = DilutionEPSPeriod
    stateMent.Net_Sales = Net_Sales
    stateMent.SalesProfit = SalesProfit
    stateMent.UnrealizedSalesProfit = UnrealizedSalesProfit
    stateMent.UnsaleFinancialAssetsUnrealizedProfit = UnsaleFinancialAssetsUnrealizedProfit
    stateMent.RemeasurementOfDefinedBenefitPlans = RemeasurementOfDefinedBenefitPlans
    stateMent.CashFlowHedgingInstrumentsProfits = CashFlowHedgingInstrumentsProfits 
    stateMent.CostOfGoodsSold = CostOfGoodsSold
    stateMent.EPSBasicIncomefromContinuingOperation = EPSBasicIncomefromContinuingOperation
    stateMent.EPSDilutionIncomefromContinuingOperation = EPSDilutionIncomefromContinuingOperation
    stateMent.SalesRevenue = SalesRevenue
    stateMent.SalesReturn = SalesReturn
    stateMent.SalesDiscount = SalesDiscount
    stateMent.ExpectedCreditImpairmentLosses = ExpectedCreditImpairmentLosses
    stateMent.ComprehensiveOtherItem = ComprehensiveOtherItem
    stateMent.InvestmentIncome = InvestmentIncome
    stateMent.RentalIncome = RentalIncome
    stateMent.OtherOperatingIncomeNet = OtherOperatingIncomeNet
    stateMent.InterestExpense = InterestExpense
    stateMent.InvestmentSpending = InvestmentSpending
    stateMent.RentalCost = RentalCost
    stateMent.OtherOperatingCosts = OtherOperatingCosts
    stateMent.save()

    # if season == "04":
    #     statement = IncomeStatement.objects.get(stock=stock, date=startDate)
    #     start_date = f'{statement.date.year}-01-01'
    #     end_date = f'{statement.date.year}-10-01'
    #     statements_before_this_season_of_the_year = IncomeStatement.objects.filter(stock=stock, date__gte = start_date, date__lte = end_date)
    #     for season_state in statements_before_this_season_of_the_year:

    #         statement.Revenue = statement.Revenue - season_state.Revenue
    #         statement.Cost = statement.Cost - season_state.Cost
    #         statement.Gross = statement.Gross - season_state.Gross

    #         statement.PromotionExpense = statement.PromotionExpense - season_state.PromotionExpense
    #         statement.ManageExpense = statement.ManageExpense - season_state.ManageExpense
    #         statement.ResearchExpense = statement.ResearchExpense - season_state.ResearchExpense
    #         statement.TotalExpense = statement.TotalExpense - season_state.TotalExpense

    #         statement.OperatingProfit = statement.OperatingProfit - season_state.OperatingProfit
    #         statement.ProfitBeforeTax = statement.ProfitBeforeTax - season_state.ProfitBeforeTax
    #         statement.ProfitAfterTax = statement.ProfitAfterTax - season_state.ProfitAfterTax
    #         statement.OtherIncome = statement.OtherIncome - season_state.OtherIncome
    #         statement.TotalIncome = statement.TotalIncome - season_state.TotalIncome

    #         statement.ParentProfit = statement.ParentProfit - season_state.ParentProfit
    #         statement.ChildProfit = statement.ChildProfit - season_state.ChildProfit
    #         statement.EPSPeriod = statement.EPSPeriod - season_state.EPSPeriod

    #         statement.save()
    
#done
@shared_task
def crawl_cash_flow_statement(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)
        
    year = startDate.year - 1911
    if startDate.month == 3:
        season = '01'
    elif startDate.month == 6:
        season = '02'
    elif startDate.month == 9:
        season = '03'
    elif startDate.month == 12:
        season = '04'

    url = f'https://mops.twse.com.tw/mops/web/t164sb05?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)
    
    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')

    table = soup.find('table',{'class':'hasBorder'})
    trs = table.find_all('tr')

    revenueBeforeTax = 0
    depreciation = 0
    amortization = 0
    interestIncome = 0
    dividendExpenditure = 0
    incomeChargesNotAffectingCash = 0
    assetsDebtsIncome = 0
    operatingCashFlow = 0
    investingCashFlow = 0
    financingCashFlow = 0
    netCashFlow = 0
    totalAssetsCash = 0
    ContinuingBusinessPreTaxNet = 0
    CurrentNetProfitBeforeTax = 0
    InterestExpense = 0
    BasedCompensationCost = 0
    RelatedCompaniesVenturesRecognised = 0
    DisposalAbandonmentPropertyProfit = 0
    DispositionOfInvestmentProfit = 0
    DisposalOfInvestmentProfit = 0
    ImpairmentLossesOnFinancialAssets = 0
    ImpairmentLossesOnNonFinancialAssets = 0
    RealisedLossOfSales = 0
    UnrealizedForeignCurrencyExchangeProfit = 0
    OtherProjects = 0
    NonAffectCashFlowTotalIncome = 0
    FinancialAssetsHeldForTrading = 0
    SafeHavenDerivativeFinancialAssets = 0
    AccountsReceivable = 0
    AccountsReceivableRelatedParty = 0
    OtherReceivablesRelatedParties = 0
    InventoryIncreaseOrDecrease = 0
    OtherCurrentAssets = 0
    OtherFinancialAssets = 0
    OperatingActivitiesNetChange = 0
    AccountsPayable = 0
    AccountsPayablePaties = 0
    ProvisionForLiabilities = 0
    OtherCurrentLiabilities = 0
    AccruedPensionLiabilities = 0
    OtherOperatingLiabilities = 0
    OperatingActivitiesLiabilitiesTotalNetChange = 0
    TotalAdjustmentItems = 0
    OperationsCashInflowOutFlow = 0
    IncomeTaxRefunded = 0
    NetCashflowFromOperatingActivities = 0
    AcquiredForSaleFinancialAssets = 0
    DisposalForSaleFinancialAssets = 0
    HeldToMaturityFinancialAssetRepayment = 0
    FinancialAssetsMeasuredAtCost = 0
    DisposalFinancialAssetsMeasuredAtCost = 0
    AcquisitionOfProperty = 0
    DisposalOfProperty = 0
    IncreasedMarginDeposit = 0
    DecreasedDeposits = 0
    AcquireIntangibleAssets = 0
    IncreaseOfOtherNonCurrentAssets = 0
    InterestReceived = 0
    NetCashInflowsFromInvestingActivities = 0
    ShortTermBorrowingIncreases = 0
    IssuingCorporateBonds = 0
    RepayCorporateDebt = 0
    RepayLongTermLoan = 0
    DepositIncreased = 0
    DepositDecreased = 0
    DecreaseInLeasePayments = 0
    EmployeeStockOptions = 0
    InterestPaid = 0
    ChangesInNonControllingInterests = 0
    OtherFundraisingActivities = 0
    NetCashFlowFromFundraising = 0
    EffectOfExchangeRateChangesOnCashEquivalents = 0
    CurrentPeriodCashEquivalents = 0
    CashEquivalentsOfBeginning = 0
    CashEquivalentsOnBalanceSheet = 0

    for item in trs:
        try:
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            print(item_title,item_content)
            if '本期稅前淨利（淨損）' in item_title:
                CurrentNetProfitBeforeTax =  item_content
            elif '不影響現金流量之收益費損項目合計' in item_title:
                NonAffectCashFlowTotalIncome =  item_content
            elif '營運產生之現金流入（流出）' in item_title:
                OperationsCashInflowOutFlow =  item_content
            elif '投資活動之淨現金流入（流出）' in item_title:
                NetCashInflowsFromInvestingActivities =  item_content
            elif '籌資活動之淨現金流入（流出）' in item_title:
                NetCashFlowFromFundraising =  item_content
            elif '本期現金及約當現金增加（減少）數' in item_title:
                CurrentPeriodCashEquivalents =  item_content
            elif '本期稅前淨利' in item_title:
                revenueBeforeTax = item_content
            elif '折舊費用' in item_title:
                depreciation =  item_content
            elif '攤銷費用' in item_title:
                amortization =  item_content
            elif '利息收入' in item_title:
                interestIncome =  item_content
            elif '股利收入' in item_title:
                dividendExpenditure =  item_content
            elif '收益費損項目合計' in item_title:
                incomeChargesNotAffectingCash =  item_content
            elif '營業活動相關之資產及負債之淨變動' in item_title:
                assetsDebtsIncome =  item_content
            elif '營運產生之現金流入' in item_title:
                operatingCashFlow =  item_content
            elif '投資活動之淨現金流入' in item_title:
                investingCashFlow =  item_content
            elif '籌資活動之淨現金流入' in item_title:
                financingCashFlow =  item_content
            elif '本期現金及約當現金增加' in item_title:
                netCashFlow =  item_content
            elif '期末現金及約當現金餘額' in item_title:
                totalAssetsCash =  item_content
            elif '繼續營業單位稅前淨利（淨損）' in item_title:
                ContinuingBusinessPreTaxNet =  item_content
            elif '利息費用' in item_title:
                InterestExpense =  item_content
            elif '股份基礎給付酬勞成本' in item_title:
                BasedCompensationCost =  item_content
            elif '採用權益法認列之關聯企業及合資損失（利益）之份額' in item_title:
                RelatedCompaniesVenturesRecognised =  item_content
            elif '處分及報廢不動產、廠房及設備損失（利益）' in item_title:
                DisposalAbandonmentPropertyProfit =  item_content
            elif '處分投資損失（利益）' in item_title:
                DispositionOfInvestmentProfit =  item_content
            elif '處分採用權益法之投資損失（利益）' in item_title:
                DisposalOfInvestmentProfit =  item_content
            elif '金融資產減損損失' in item_title:
                ImpairmentLossesOnFinancialAssets =  item_content
            elif '非金融資產減損損失' in item_title:
                ImpairmentLossesOnNonFinancialAssets =  item_content
            elif '已實現銷貨損失（利益）' in item_title:
                RealisedLossOfSales =  item_content
            elif '未實現外幣兌換損失（利益）' in item_title:
                UnrealizedForeignCurrencyExchangeProfit =  item_content
            elif '其他項目' in item_title:
                OtherProjects =  item_content
            elif '持有供交易之金融資產（增加）減少' in item_title:
                FinancialAssetsHeldForTrading =  item_content
            elif '避險之衍生金融資產（增加）減少' in item_title:
                SafeHavenDerivativeFinancialAssets =  item_content
            elif '應收帳款（增加）減少' in item_title:
                AccountsReceivable =  item_content
            elif '應收帳款－關係人（增加）減少' in item_title:
                AccountsReceivableRelatedParty =  item_content
            elif '其他應收款－關係人（增加）減少' in item_title:
                OtherReceivablesRelatedParties =  item_content
            elif '存貨（增加）減少' in item_title:
                InventoryIncreaseOrDecrease =  item_content
            elif '其他流動資產（增加）減少' in item_title:
                OtherCurrentAssets =  item_content
            elif '其他金融資產（增加）減少' in item_title:
                OtherFinancialAssets =  item_content
            elif '與營業活動相關之資產之淨變動合計' in item_title:
                OperatingActivitiesNetChange =  item_content
            elif '應付帳款增加（減少）' in item_title:
                AccountsPayable =  item_content
            elif '應付帳款－關係人增加（減少）' in item_title:
                AccountsPayablePaties =  item_content
            elif '負債準備增加（減少）' in item_title:
                ProvisionForLiabilities =  item_content
            elif '其他流動負債增加（減少）' in item_title:
                OtherCurrentLiabilities =  item_content
            elif '應計退休金負債增加（減少）' in item_title:
                AccruedPensionLiabilities =  item_content
            elif '其他營業負債增加（減少）' in item_title:
                OtherOperatingLiabilities =  item_content
            elif '與營業活動相關之負債之淨變動合計' in item_title:
                OperatingActivitiesLiabilitiesTotalNetChange =  item_content
            elif '調整項目合計' in item_title:
                TotalAdjustmentItems =  item_content
            elif '退還（支付）之所得稅' in item_title:
                IncomeTaxRefunded =  item_content
            elif '營業活動之淨現金流入（流出）' in item_title:
                NetCashflowFromOperatingActivities = item_content
            elif '取得備供出售金融資產' in item_title:
                AcquiredForSaleFinancialAssets =  item_content
            elif '處分備供出售金融資產' in item_title:
                DisposalForSaleFinancialAssets =  item_content
            elif '持有至到期日金融資產到期還本' in item_title:
                HeldToMaturityFinancialAssetRepayment =  item_content
            elif '取得以成本衡量之金融資產' in item_title:
                FinancialAssetsMeasuredAtCost =  item_content
            elif '處分以成本衡量之金融資產' in item_title:
                DisposalFinancialAssetsMeasuredAtCost =  item_content
            elif '取得不動產、廠房及設備' in item_title:
                AcquisitionOfProperty =  item_content
            elif '處分不動產、廠房及設備' in item_title:
                DisposalOfProperty =  item_content
            elif '存出保證金增加' in item_title:
                IncreasedMarginDeposit =  item_content
            elif '存出保證金減少' in item_title:
                DecreasedDeposits =  item_content
            elif '取得無形資產' in item_title:
                AcquireIntangibleAssets =  item_content
            elif '其他非流動資產增加' in item_title:
                IncreaseOfOtherNonCurrentAssets =  item_content
            elif '收取之利息' in item_title:
                InterestReceived =  item_content
            elif '短期借款增加' in item_title:
                ShortTermBorrowingIncreases =  item_content
            elif '發行公司債' in item_title:
                IssuingCorporateBonds =  item_content
            elif '償還公司債' in item_title:
                RepayCorporateDebt =  item_content
            elif '償還長期借款' in item_title:
                RepayLongTermLoan =  item_content
            elif '存入保證金增加' in item_title:
                DepositIncreased =  item_content
            elif '存入保證金減少' in item_title:
                DepositDecreased =  item_content
            elif '應付租賃款減少' in item_title:
                DecreaseInLeasePayments =  item_content
            elif '員工執行認股權' in item_title:
                EmployeeStockOptions =  item_content
            elif '支付之利息' in item_title:
                InterestPaid =  item_content
            elif '非控制權益變動' in item_title:
                ChangesInNonControllingInterests =  item_content
            elif '其他籌資活動' in item_title:
                OtherFundraisingActivities =  item_content
            elif '匯率變動對現金及約當現金之影響' in item_title:
                EffectOfExchangeRateChangesOnCashEquivalents =  item_content
            elif '期初現金及約當現金餘額' in item_title:
                CashEquivalentsOfBeginning =  item_content
            elif '資產負債表帳列之現金及約當現金' in item_title:
                CashEquivalentsOnBalanceSheet =  item_content

        except:
            print('this tr no content')

    if CashFlowStatement.objects.filter(stock=stock, date=startDate).count() == 0:
        stateMent = CashFlowStatement()
    else:
        stateMent = CashFlowStatement.objects.get(stock=stock, date=startDate)

    stateMent.stock_code = stock_code
    stateMent.stock = stock
    stateMent.date = startDate
    stateMent.RevenueBeforeTax = revenueBeforeTax
    stateMent.Depreciation = depreciation
    stateMent.Amortization = amortization
    stateMent.InterestIncome = interestIncome
    stateMent.DividendExpenditure = dividendExpenditure
    stateMent.IncomeChargesNotAffectingCash = incomeChargesNotAffectingCash
    stateMent.AssetsDebtsIncome = assetsDebtsIncome
    stateMent.OperatingCashFlow = operatingCashFlow
    stateMent.InvestingCashFlow = investingCashFlow
    stateMent.FinancingCashFlow = financingCashFlow
    stateMent.NetCashFlow = netCashFlow
    stateMent.TotalAssetsCash = totalAssetsCash
    stateMent.ContinuingBusinessPreTaxNet = ContinuingBusinessPreTaxNet
    stateMent.CurrentNetProfitBeforeTax = CurrentNetProfitBeforeTax
    stateMent.InterestExpense = InterestExpense
    stateMent.BasedCompensationCost = BasedCompensationCost
    stateMent.RelatedCompaniesVenturesRecognised = RelatedCompaniesVenturesRecognised
    stateMent.DisposalAbandonmentPropertyProfit = DisposalAbandonmentPropertyProfit
    stateMent.DispositionOfInvestmentProfit = DispositionOfInvestmentProfit
    stateMent.DisposalOfInvestmentProfit = DisposalOfInvestmentProfit
    stateMent.ImpairmentLossesOnFinancialAssets = ImpairmentLossesOnFinancialAssets
    stateMent.ImpairmentLossesOnNonFinancialAssets = ImpairmentLossesOnNonFinancialAssets
    stateMent.RealisedLossOfSales = RealisedLossOfSales
    stateMent.UnrealizedForeignCurrencyExchangeProfit = UnrealizedForeignCurrencyExchangeProfit
    stateMent.OtherProjects = OtherProjects
    stateMent.NonAffectCashFlowTotalIncome = NonAffectCashFlowTotalIncome
    stateMent.FinancialAssetsHeldForTrading = FinancialAssetsHeldForTrading
    stateMent.SafeHavenDerivativeFinancialAssets = SafeHavenDerivativeFinancialAssets
    stateMent.AccountsReceivable = AccountsReceivable
    stateMent.AccountsReceivableRelatedParty = AccountsReceivableRelatedParty
    stateMent.OtherReceivablesRelatedParties = OtherReceivablesRelatedParties
    stateMent.InventoryIncreaseOrDecrease = InventoryIncreaseOrDecrease
    stateMent.OtherCurrentAssets = OtherCurrentAssets
    stateMent.OtherFinancialAssets = OtherFinancialAssets
    stateMent.OperatingActivitiesNetChange = OperatingActivitiesNetChange
    stateMent.AccountsPayable = AccountsPayable
    stateMent.AccountsPayablePaties = AccountsPayablePaties
    stateMent.ProvisionForLiabilities = ProvisionForLiabilities
    stateMent.OtherCurrentLiabilities = OtherCurrentLiabilities
    stateMent.AccruedPensionLiabilities = AccruedPensionLiabilities
    stateMent.OtherOperatingLiabilities = OtherOperatingLiabilities
    stateMent.OperatingActivitiesLiabilitiesTotalNetChange = OperatingActivitiesLiabilitiesTotalNetChange
    stateMent.TotalAdjustmentItems = TotalAdjustmentItems
    stateMent.OperationsCashInflowOutFlow = OperationsCashInflowOutFlow
    stateMent.IncomeTaxRefunded = IncomeTaxRefunded
    stateMent.NetCashflowFromOperatingActivities = NetCashflowFromOperatingActivities
    stateMent.AcquiredForSaleFinancialAssets = AcquiredForSaleFinancialAssets
    stateMent.DisposalForSaleFinancialAssets = DisposalForSaleFinancialAssets
    stateMent.HeldToMaturityFinancialAssetRepayment = HeldToMaturityFinancialAssetRepayment
    stateMent.FinancialAssetsMeasuredAtCost = FinancialAssetsMeasuredAtCost
    stateMent.DisposalFinancialAssetsMeasuredAtCost = DisposalFinancialAssetsMeasuredAtCost
    stateMent.AcquisitionOfProperty = AcquisitionOfProperty
    stateMent.DisposalOfProperty = DisposalOfProperty
    stateMent.IncreasedMarginDeposit = IncreasedMarginDeposit
    stateMent.DecreasedDeposits = DecreasedDeposits
    stateMent.AcquireIntangibleAssets = AcquireIntangibleAssets
    stateMent.IncreaseOfOtherNonCurrentAssets = IncreaseOfOtherNonCurrentAssets
    stateMent.InterestReceived = InterestReceived
    stateMent.NetCashInflowsFromInvestingActivities = NetCashInflowsFromInvestingActivities
    stateMent.ShortTermBorrowingIncreases = ShortTermBorrowingIncreases
    stateMent.IssuingCorporateBonds = IssuingCorporateBonds
    stateMent.RepayCorporateDebt = RepayCorporateDebt
    stateMent.RepayLongTermLoan = RepayLongTermLoan
    stateMent.DepositIncreased = DepositIncreased
    stateMent.Amortization = amortization
    stateMent.InterestIncome = interestIncome
    stateMent.DepositDecreased = DepositDecreased
    stateMent.DecreaseInLeasePayments = DecreaseInLeasePayments
    stateMent.EmployeeStockOptions = EmployeeStockOptions
    stateMent.InterestPaid = InterestPaid
    stateMent.ChangesInNonControllingInterests = ChangesInNonControllingInterests
    stateMent.OtherFundraisingActivities = OtherFundraisingActivities
    stateMent.NetCashFlowFromFundraising = NetCashFlowFromFundraising
    stateMent.EffectOfExchangeRateChangesOnCashEquivalents = EffectOfExchangeRateChangesOnCashEquivalents
    stateMent.CurrentPeriodCashEquivalents = CurrentPeriodCashEquivalents
    stateMent.CashEquivalentsOfBeginning = CashEquivalentsOfBeginning
    stateMent.CashEquivalentsOnBalanceSheet = CashEquivalentsOnBalanceSheet

    stateMent.save()

#done
@shared_task
def crawl_dividend_policy(stock_code):
    stock = Stock.objects.get(stock_code=stock_code)
    
    url = f'https://goodinfo.tw/StockInfo/StockDividendPolicy.asp?STOCK_ID={stock_code}&SHOW_ROTC='
    print(url)

    # headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'}
    # resp = requests.get(url, headers =headers)
    
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'lxml')
    table = soup.find(id = 'divDividendDetailData')
    trs = table.find_all('tr',{'align':'center'})

    # print(trs)

    for index,item in enumerate(trs):
        # print('股利發放年度'+ item.find_all('td')[0].getText())
        if item.find_all('td')[19].getText() != '-':
            period = item.find_all('td')[19].getText()

            # print(period)

            if '∟' in item.find_all('td')[0].getText() and '~' in period:
                period = period[:period.index('~')]
            
            # print(period)

            if '~' not in period and '累計' not in period:
                if 'Q' not in period:
                    date = datetime(int(period),12, 31)
                elif 'Q1' in period:
                    year = '20' + period[:2]
                    date = datetime(int(year),3, 31)
                elif 'Q2' in period:
                    year = '20' + period[:2]
                    date = datetime(int(year),6, 30)
                elif 'Q3' in period:
                    year = '20' + period[:2]
                    date = datetime(int(year),9, 30)
                elif 'Q4' in period:
                    year = '20' + period[:2]
                    date = datetime(int(year),12, 31)

                if DividendSheet.objects.filter(stock_code=stock_code, date=date).count() == 0:
                    sheet = DividendSheet()
                    sheet.date = date
                    sheet.stock = stock
                    sheet.stock_code = stock_code
                    try:
                        sheet.CashDividend = float(item.find_all('td')[3].getText().replace(',',''))
                    except:
                        sheet.CashDividend = 0

                    try:
                        sheet.ShareDividend = float(item.find_all('td')[6].getText().replace(',',''))
                    except:
                        sheet.ShareDividend = 0

                    try:
                        sheet.EPS = float(item.find_all('td')[20].getText().replace(',',''))
                    except:
                        sheet.EPS = 0

                    try:
                        sheet.DividendPayoutRatio = float(item.find_all('td')[23].getText().replace(',',''))
                    except:
                        sheet.DividendPayoutRatio = 0
                    
                    if item.find_all('td')[15].getText() != '-':
                        sheet.AverageStockPrice = float(item.find_all('td')[15].getText().replace(',',''))
                    else:
                        sheet.AverageStockPrice = 0

                    if item.find_all('td')[18].getText() != '-':
                        sheet.YieldRate = float(item.find_all('td')[18].getText().replace(',',''))
                    else:
                        sheet.YieldRate = 0

                    if item.find_all('td')[10].getText() != '-':
                        sheet.DaysReturnExPrice = int(item.find_all('td')[10].getText().replace(',',''))
                    elif item.find_all('td')[11].getText() != '-':
                        sheet.DaysReturnExPrice = int(item.find_all('td')[11].getText().replace(',',''))
                    else:
                        sheet.DaysReturnExPrice = 0
                    sheet.save()
            

        else:
            if item.find_all('td')[0].getText() != '∟'  and  trs[index+1].find_all('td')[0].getText() != '∟':
                date = datetime(int(item.find_all('td')[0].getText()), 12, 31)
            elif item.find_all('td')[0].getText() != '∟' and trs[index+1].find_all('td')[0].getText() == '∟':
                date = None
            elif item.find_all('td')[0].getText() == '∟':
                i = 1
                while trs[index-i].find_all('td')[0].getText() == '∟':
                    i= i+1
                current_year = trs[index-i].find_all('td')[0].getText()

                if i==1:
                    date = datetime(int(current_year), 3, 31)
                elif i==2:
                    date = datetime(int(current_year), 6, 30)
                elif i==3:
                    date = datetime(int(current_year), 9, 30)
                elif i==4:
                    date = datetime(int(current_year), 12, 31)
            
            # print(date)

            if date != None and DividendSheet.objects.filter(stock_code=stock_code, date=date).count() == 0:

                sheet = DividendSheet()
                sheet.date = date
                sheet.stock = stock
                sheet.stock_code = stock_code
                try:
                    sheet.CashDividend = float(item.find_all('td')[3].getText().replace(',',''))
                except:
                    sheet.CashDividend = 0

                try:
                    sheet.ShareDividend = float(item.find_all('td')[6].getText().replace(',',''))
                except:
                    sheet.ShareDividend = 0

                try:
                    sheet.EPS = float(item.find_all('td')[20].getText().replace(',',''))
                except:
                    sheet.EPS = 0

                try:
                    sheet.DividendPayoutRatio = float(item.find_all('td')[23].getText().replace(',',''))
                except:
                    sheet.DividendPayoutRatio = 0
                
                if item.find_all('td')[15].getText() != '-':
                    sheet.AverageStockPrice = float(item.find_all('td')[15].getText().replace(',',''))
                else:
                    sheet.AverageStockPrice = 0

                if item.find_all('td')[18].getText() != '-':
                    sheet.YieldRate = float(item.find_all('td')[18].getText().replace(',',''))
                else:
                    sheet.YieldRate = 0

                if item.find_all('td')[10].getText() != '-':
                    sheet.DaysReturnExPrice = int(item.find_all('td')[10].getText().replace(',',''))
                elif item.find_all('td')[11].getText() != '-':
                    sheet.DaysReturnExPrice = int(item.find_all('td')[11].getText().replace(',',''))
                else:
                    sheet.DaysReturnExPrice = 0
                sheet.save()

            # print('現金股利合計'+ item.find_all('td')[3].getText())
            # print('股票股利合計'+ item.find_all('td')[6].getText())
            # print('股利合計'+ item.find_all('td')[7].getText())
            # print('股價統計年均	(元)'+ item.find_all('td')[15].getText())
            # print('年均殖利率(%)合計'+ item.find_all('td')[18].getText())
            # print('股利所屬期間'+ item.find_all('td')[19].getText())
            # print('EPS(元)'+ item.find_all('td')[20].getText())
            # print('盈餘分配率(%)合計'+ item.find_all('td')[23].getText())

    time.sleep(random.randint(5,10))

#GrowthRate1Year start from second data, EPSGrowthRate5Years start from fifth data
@shared_task
def calculate_season_key_values(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.filter(stock_code=stock_code)[0]
    print(f'calculate season key value stock_id={stock.id} {stock.name} {date_string} stock_code={stock.stock_code}')

    try:
        cashFlowStatement = CashFlowStatement.objects.get(date=startDate, stock = stock)
    except:
        cashFlowStatement = get_closest_to( CashFlowStatement.objects.filter(stock = stock), startDate.date())

    try:
        balanceSheet = BalanceSheet.objects.get(date=startDate, stock = stock)
    except:
        balanceSheet = get_closest_to( BalanceSheet.objects.filter(stock = stock), startDate.date())

    try:
        incomeStatement = IncomeStatement.objects.get(date=startDate, stock = stock)
    except:
        incomeStatement = get_closest_to( IncomeStatement.objects.filter(stock = stock), startDate.date())

    try:
        dividendSheet = DividendSheet.objects.get(date=startDate, stock = stock)
    except:
        dividendSheet = DividendSheet()
    
    # try:
    if StockRecord.objects.filter(date=startDate, stock = stock).count() != 0:
        price = StockRecord.objects.filter(date=startDate, stock = stock)[0].ClosingPrice
    else:
        #get lastest price
        price = get_closest_to(StockRecord.objects.filter(stock=stock), startDate.date()).ClosingPrice
    
    last_12_months_date = incomeStatement.date - timedelta(days=360)
    last_12_months_states = IncomeStatement.objects.filter(stock=stock, date__gte = last_12_months_date, date__lte = incomeStatement.date)
    last_12_months_eps = sum(last_12_months_states.values_list('EPS_Period', flat=True))
    
    try:
        PriceEarningRatio = price / last_12_months_eps
    except:
        PriceEarningRatio = 0

    EPS = incomeStatement.EPS_Period

    #這裡應該要再修正,有的公司每年發股利, 有的每季發, 統一用 4 季累加比較公平~
    #單位千元
    MarketValue = balanceSheet.Equity_CommonStock /10 * price  
    Dividend = dividendSheet.CashDividend + dividendSheet.ShareDividend
    Yield = dividendSheet.YieldRate

    try:
        ReturnOfEquity = incomeStatement.ProfitAfterTax / balanceSheet.Equity_Total
    except:
        ReturnOfEquity = 0
    
    try:
        ReturnOfAssets = incomeStatement.ProfitAfterTax / balanceSheet.AssetsTotal
    except:
        ReturnOfAssets = 0

    try:
        PriceBookRatio =  price / balanceSheet.Equity_Per_Share
    except:
        PriceBookRatio = 0
    
    if(incomeStatement.Revenue <= 0):
        GrossMargin = 0
    else:
        try:
            GrossMargin = incomeStatement.Gross / incomeStatement.Revenue
        except:
            GrossMargin = 0

    if(incomeStatement.Revenue <= 0):
        OperatingMargin = 0
    else:
        try:
            OperatingMargin = incomeStatement.OperatingProfit / incomeStatement.Revenue
        except:
            OperatingMargin = 0

    if(incomeStatement.Revenue <= 0):
        NetProfitAfterTaxMargin = 0
    else:
        try:
            NetProfitAfterTaxMargin = incomeStatement.ProfitAfterTax / incomeStatement.Revenue
        except:
            NetProfitAfterTaxMargin = 0

    try:
        DebtAssetRatio = balanceSheet.DebtTotal / balanceSheet.AssetsTotal
    except:
        DebtAssetRatio = 0

    EpsGrowthRateArray = []
    ROEGrowthRateArray = []
    RevenueGrowthRateArray = []
    this_year_eps = EPS
    this_year_roe = ReturnOfEquity * 100
    this_year_revenue = incomeStatement.Revenue
    EPSGrowthRate1Year = 0
    ROEGrowthRate1Year = 0
    RevenueGrowthRate1Year = 0
    EPSGrowthRate5Years = 0
    ROEGrowthRate5Years = 0
    RevenueGrowthRate5Years = 0

    i = 1
    while i <= 5:
        theDate = datetime(startDate.year-i,startDate.month,startDate.day)

        try:
            thekeyValueSheetSeason = KeyValueSheetSeason.objects.get(date=theDate, stock = stock)
            theIncomeStatement = IncomeStatement.objects.get(date=theDate, stock = stock)
            
            epsGrowthRate = (this_year_eps - thekeyValueSheetSeason.EPS)/thekeyValueSheetSeason.EPS
            EpsGrowthRateArray.append(epsGrowthRate)
            
            # print("this year roe")
            # print(this_year_roe)
            # print("last year roe")
            # print(thekeyValueSheetSeason.ReturnOfEquity)

            roeGrowthRate = (this_year_roe - thekeyValueSheetSeason.ReturnOfEquity)/thekeyValueSheetSeason.ReturnOfEquity
            ROEGrowthRateArray.append(roeGrowthRate)

            revenueGrowthRate = (this_year_revenue - theIncomeStatement.Revenue)/theIncomeStatement.Revenue
            RevenueGrowthRateArray.append(revenueGrowthRate)

            this_year_eps = thekeyValueSheetSeason.EPS
            this_year_roe = thekeyValueSheetSeason.ReturnOfEquity
            this_year_revenue = theIncomeStatement.Revenue

            i = i + 1
        except:
            print("can't find keyValueSheetSeason")
            break
    
    if len(EpsGrowthRateArray) != 0 and len(ROEGrowthRateArray) != 0 and len(RevenueGrowthRateArray) !=0 :
        EPSGrowthRate1Year = EpsGrowthRateArray[0]
        ROEGrowthRate1Year = ROEGrowthRateArray[0]
        RevenueGrowthRate1Year = RevenueGrowthRateArray[0]

    if len(EpsGrowthRateArray) == 5 and len(ROEGrowthRateArray) == 5 and len(RevenueGrowthRateArray) ==5:
        EPSGrowthRate5Years = sum(EpsGrowthRateArray)/5
        ROEGrowthRate5Years = sum(ROEGrowthRateArray)/5
        RevenueGrowthRate5Years = sum(RevenueGrowthRateArray)/5

    try:
        NetProfitBeforeTaxMargin =  incomeStatement.ProfitBeforeTax / incomeStatement.Revenue
    except:
        NetProfitBeforeTaxMargin = 0

    CommonStockShares = balanceSheet.Equity_CommonStock*1000/10
    DirectorSupervisorShareRatio = balanceSheet.DirectorSupervisorShares / CommonStockShares

    last_12_months_date = incomeStatement.date - timedelta(days=360)
    last_12_months_sheets = DividendSheet.objects.filter(stock=stock, date__gte = last_12_months_date, date__lte = incomeStatement.date)
    last_12_months_CashDividend = sum(last_12_months_sheets.values_list('CashDividend', flat=True))
    last_12_months_ShareDividend = sum(last_12_months_sheets.values_list('ShareDividend', flat=True))
    total_dividends = last_12_months_CashDividend + last_12_months_ShareDividend

    try:
        DividendPayoutRatio = total_dividends / last_12_months_eps * 100
    except:
        DividendPayoutRatio = 0
    
    if DividendPayoutRatio > 100:
        DividendPayoutRatio = 0
    elif DividendPayoutRatio < -100:
        DividendPayoutRatio = -0

    ReferenceStockPrice = price
    
    CashFlowPerShare = cashFlowStatement.NetCashFlow*1000 / CommonStockShares

    try:
        DirectorSupervisorPledgeShareRatio = balanceSheet.DirectorSupervisorPledgeShares / balanceSheet.DirectorSupervisorShares
    except:
        DirectorSupervisorPledgeShareRatio = 0


    if KeyValueSheetSeason.objects.filter(stock= stock, date = startDate).count() == 0:
        keyValueSheetSeason = KeyValueSheetSeason()
    else:
        keyValueSheetSeason = KeyValueSheetSeason.objects.filter(stock= stock, date = startDate)[0]

    keyValueSheetSeason.stock = stock
    keyValueSheetSeason.stock_code = stock_code
    keyValueSheetSeason.category = stock.category
    keyValueSheetSeason.date = startDate

    if PriceEarningRatio > 1000:
        PriceEarningRatio = 0
    elif PriceEarningRatio < -1000:
        PriceEarningRatio = -0
    keyValueSheetSeason.PriceEarningRatio = PriceEarningRatio
    # keyValueSheetSeason.save()

    keyValueSheetSeason.MarketValue = MarketValue
    # keyValueSheetSeason.save()

    keyValueSheetSeason.Dividend = Dividend
    # keyValueSheetSeason.save()

    keyValueSheetSeason.EPS = EPS
    # keyValueSheetSeason.save()
    
    if Yield > 1000:
        Yield = 0
    elif Yield < -1000:
        Yield = -0
    keyValueSheetSeason.Yield = Yield
    # keyValueSheetSeason.save()

    if ReturnOfEquity *100 > 1000:
        ReturnOfEquity = 0
    elif ReturnOfEquity *100 < -1000:
        ReturnOfEquity = -0
    keyValueSheetSeason.ReturnOfEquity = ReturnOfEquity * 100
    # keyValueSheetSeason.save()

    if ReturnOfAssets *100 > 1000:
        ReturnOfAssets = 0
    elif ReturnOfAssets *100 < -1000:
        ReturnOfAssets = -0
    keyValueSheetSeason.ReturnOfAssets = ReturnOfAssets *100
    # keyValueSheetSeason.save()

    if PriceBookRatio > 1000:
        PriceBookRatio = 0
    elif PriceBookRatio < -1000:
        PriceBookRatio = -0
    keyValueSheetSeason.PriceBookRatio = PriceBookRatio 
    # keyValueSheetSeason.save()

    if GrossMargin *100 > 1000:
        GrossMargin = 0
    elif GrossMargin *100 < -1000:
        GrossMargin = -0
    keyValueSheetSeason.GrossMargin = GrossMargin *100
    # keyValueSheetSeason.save()

    if OperatingMargin *100 > 1000:
        OperatingMargin = 0
    elif OperatingMargin *100 < -1000:
        OperatingMargin = -0
    keyValueSheetSeason.OperatingMargin = OperatingMargin *100   
    # keyValueSheetSeason.save()

    if NetProfitAfterTaxMargin *100 > 1000:
        NetProfitAfterTaxMargin = 0
    elif NetProfitAfterTaxMargin *100 < -1000:
        NetProfitAfterTaxMargin = -0
    keyValueSheetSeason.NetProfitAfterTaxMargin = NetProfitAfterTaxMargin *100
    # keyValueSheetSeason.save()

    if DebtAssetRatio *100 > 1000:
        DebtAssetRatio = 0
    elif DebtAssetRatio *100 < -1000:
        DebtAssetRatio = -0
    keyValueSheetSeason.DebtAssetRatio = DebtAssetRatio *100
    # keyValueSheetSeason.save()

    if EPSGrowthRate5Years *100 > 1000:
        EPSGrowthRate5Years = 0
    elif EPSGrowthRate5Years *100 < -1000:
        EPSGrowthRate5Years = -0
    keyValueSheetSeason.EPSGrowthRate5Years = EPSGrowthRate5Years *100
    # keyValueSheetSeason.save()

    if ROEGrowthRate5Years *100 > 1000:
        ROEGrowthRate5Years = 0
    elif ROEGrowthRate5Years *100 < -1000:
        ROEGrowthRate5Years = -0
    keyValueSheetSeason.ROEGrowthRate5Years = ROEGrowthRate5Years *100
    # keyValueSheetSeason.save()

    if RevenueGrowthRate5Years *100 > 1000:
        RevenueGrowthRate5Years = 0
    elif RevenueGrowthRate5Years *100 < -1000:
        RevenueGrowthRate5Years = -0
    keyValueSheetSeason.RevenueGrowthRate5Years = RevenueGrowthRate5Years *100
    # keyValueSheetSeason.save()

    if EPSGrowthRate1Year *100 > 1000:
        EPSGrowthRate1Year = 0
    elif EPSGrowthRate1Year *100 < -1000:
        EPSGrowthRate1Year = -0
    keyValueSheetSeason.EPSGrowthRate1Year = EPSGrowthRate1Year *100
    # keyValueSheetSeason.save()

    if ROEGrowthRate1Year *100 > 1000:
        ROEGrowthRate1Year = 0
    elif ROEGrowthRate1Year *100 < -1000:
        ROEGrowthRate1Year = -0
    keyValueSheetSeason.ROEGrowthRate1Year = ROEGrowthRate1Year *100
    # keyValueSheetSeason.save()

    if RevenueGrowthRate1Year *100 > 1000:
        RevenueGrowthRate1Year = 0
    elif RevenueGrowthRate1Year *100 < -1000:
        RevenueGrowthRate1Year = -0
    keyValueSheetSeason.RevenueGrowthRate1Year = RevenueGrowthRate1Year *100
    # keyValueSheetSeason.save()
    
    if NetProfitBeforeTaxMargin *100 > 100:
        NetProfitBeforeTaxMargin = 0
    elif NetProfitBeforeTaxMargin *100 < -100:
        NetProfitBeforeTaxMargin = -0
    keyValueSheetSeason.NetProfitBeforeTaxMargin = NetProfitBeforeTaxMargin *100
    # keyValueSheetSeason.save()

    if DirectorSupervisorShareRatio *100 > 1000:
        DirectorSupervisorShareRatio = 0
    elif DirectorSupervisorShareRatio *100 < -1000:
        DirectorSupervisorShareRatio = -0
    keyValueSheetSeason.DirectorSupervisorShareRatio = DirectorSupervisorShareRatio*100
    # keyValueSheetSeason.save()

    keyValueSheetSeason.DividendPayoutRatio = DividendPayoutRatio
    keyValueSheetSeason.save()

    keyValueSheetSeason.CommonStockShares = CommonStockShares
    # keyValueSheetSeason.save()

    keyValueSheetSeason.ReferenceStockPrice = ReferenceStockPrice
    # keyValueSheetSeason.save()

    keyValueSheetSeason.CashFlowPerShare = CashFlowPerShare
    # keyValueSheetSeason.save()

    if DirectorSupervisorPledgeShareRatio *100 > 1000:
        DirectorSupervisorPledgeShareRatio = 0
    elif DirectorSupervisorPledgeShareRatio *100 < -1000:
        DirectorSupervisorPledgeShareRatio = -0
    keyValueSheetSeason.DirectorSupervisorPledgeShareRatio = DirectorSupervisorPledgeShareRatio*100

    keyValueSheetSeason.save()
    
    # except:
    #     print(f'error!!! calculate season key value {stock.name} {date_string}')

#calculate current key value, should be done every marketing
@shared_task
def calculate_current_key_values(stock_code):

    stock = Stock.objects.get(stock_code=stock_code)
    theday = StockRecord.objects.filter(stock=stock).order_by('-date')[0].date
    print(theday.strftime("%Y/%m/%d/") + stock.name + ' '+ stock.stock_code)
    price = StockRecord.objects.filter(stock=stock).order_by('-date')[0].ClosingPrice

    balanceSheet = BalanceSheet.objects.filter(stock = stock).order_by('-date')[0]
    incomeStatement = IncomeStatement.objects.filter(stock = stock).order_by('-date')[0]

    try:
        PriceEarningRatio = price / incomeStatement.EPS_Period
    except:
        PriceEarningRatio = 0

    #單位千元
    try:
        MarketValue = balanceSheet.Equity_CommonStock /10 * price
    except:
        MarketValue = 0

    resentKeyValueSeasons = KeyValueSheetSeason.objects.filter(stock_code=stock_code).order_by('-date')[0:4]

    if KeyValueSheetCurrent.objects.filter(stock=stock).count() == 0:
        keyValueSheetCurrent = KeyValueSheetCurrent()
    else:
        keyValueSheetCurrent = KeyValueSheetCurrent.objects.get(stock=stock)
    

    CommonStockShares = balanceSheet.Equity_CommonStock*1000/10

    cashFlowStatement = CashFlowStatement.objects.filter(stock = stock).order_by('-date')[0]
    query_date = f'{cashFlowStatement.date.year-1}-12-31'
    if cashFlowStatement.date.month != 12 and CashFlowStatement.objects.filter(stock = stock, date=query_date).count() != 0:   
        cashFlowStatement = CashFlowStatement.objects.filter(stock = stock, date=query_date)[0]
    
    try:
        yearCashflowPerShare = cashFlowStatement.NetCashFlow*1000 / CommonStockShares
    except:
        yearCashflowPerShare = 0

    yearEPS = 0 
    yearDividend = 0
    yearReturnOfEquity = 0
    yearReturnOfAssets = 0
    
    yearPayoutRatio = 0
    yearYield = 0
    yearPriceEarningRatio = 0

    for sheet in resentKeyValueSeasons:
        yearEPS = yearEPS + sheet.EPS
        yearDividend = yearDividend + sheet.Dividend
        yearReturnOfEquity = yearReturnOfEquity + sheet.ReturnOfEquity
        yearReturnOfAssets = yearReturnOfAssets + sheet.ReturnOfAssets

    try:
        yearPayoutRatio = yearDividend / yearEPS * 100
    except:
        yearPayoutRatio = 0

    if yearPayoutRatio > 10000:
        yearPayoutRatio = 9999
    elif yearPayoutRatio < -10000:
        yearPayoutRatio = -9999

    yearYield = yearDividend / price * 100
    
    if yearYield > 10000:
        yearYield = 9999
    elif yearYield < -10000:
        yearYield = -9999

    try:
        yearPriceEarningRatio = price / yearEPS
    except:
        yearPriceEarningRatio = 0

    if yearPriceEarningRatio > 10000:
        yearPriceEarningRatio = 9999
    elif yearPriceEarningRatio < -10000:
        yearPriceEarningRatio = -9999

    bookValue = balanceSheet.Equity_Per_Share
    try:
        priceBookRatio = price / bookValue
    except:
        priceBookRatio = 0

    keyValueSheetCurrent.stock = stock
    keyValueSheetCurrent.stock_code = stock_code
    keyValueSheetCurrent.stock_name = stock.name
    keyValueSheetCurrent.date = theday
    keyValueSheetCurrent.category = stock.category
    keyValueSheetCurrent.PriceEarningRatio = yearPriceEarningRatio
    keyValueSheetCurrent.MarketValue = MarketValue
    keyValueSheetCurrent.Dividend = yearDividend
    keyValueSheetCurrent.EPS = yearEPS
    keyValueSheetCurrent.Yield = yearYield
    keyValueSheetCurrent.ReturnOfEquity = yearReturnOfEquity
    keyValueSheetCurrent.ReturnOfAssets = yearReturnOfAssets

    keyValueSheetCurrent.PriceBookRatio = priceBookRatio
    keyValueSheetCurrent.Equity_Per_Share = bookValue

    keyValueSheetCurrent.GrossMargin = resentKeyValueSeasons[0].GrossMargin
    keyValueSheetCurrent.OperatingMargin = resentKeyValueSeasons[0].OperatingMargin    
    keyValueSheetCurrent.NetProfitAfterTaxMargin = resentKeyValueSeasons[0].NetProfitAfterTaxMargin      
    keyValueSheetCurrent.DebtAssetRatio = resentKeyValueSeasons[0].DebtAssetRatio
    keyValueSheetCurrent.EPSGrowthRate5Years = resentKeyValueSeasons[0].EPSGrowthRate5Years      
    keyValueSheetCurrent.ROEGrowthRate5Years = resentKeyValueSeasons[0].ROEGrowthRate5Years  
    keyValueSheetCurrent.RevenueGrowthRate5Years = resentKeyValueSeasons[0].RevenueGrowthRate5Years      
    keyValueSheetCurrent.EPSGrowthRate1Year = resentKeyValueSeasons[0].EPSGrowthRate1Year   
    keyValueSheetCurrent.ROEGrowthRate1Year = resentKeyValueSeasons[0].ROEGrowthRate1Year
    keyValueSheetCurrent.RevenueGrowthRate1Year = resentKeyValueSeasons[0].RevenueGrowthRate1Year
    keyValueSheetCurrent.NetProfitBeforeTaxMargin = resentKeyValueSeasons[0].NetProfitBeforeTaxMargin
    keyValueSheetCurrent.DirectorSupervisorShareRatio = resentKeyValueSeasons[0].DirectorSupervisorShareRatio
    keyValueSheetCurrent.DividendPayoutRatio = yearPayoutRatio    
    keyValueSheetCurrent.CommonStockShares = resentKeyValueSeasons[0].CommonStockShares   

    keyValueSheetCurrent.CurrentStockPrice = price
    keyValueSheetCurrent.ClosingPrice = price           
    keyValueSheetCurrent.CashFlowPerShare = yearCashflowPerShare              
    keyValueSheetCurrent.DirectorSupervisorPledgeShareRatio = resentKeyValueSeasons[0].DirectorSupervisorPledgeShareRatio
    keyValueSheetCurrent.save()

@shared_task
def calculate_stock_evalutate(stock_code, date_string):
 
    stock = Stock.objects.get(stock_code=stock_code)
    allKeySheets = KeyValueSheetCurrent.objects.all()
    
    print('evaluate ' + date_string + stock.name + stock.stock_code)

    if StockEvaluate.objects.filter(stock=stock).count()!=0:
        stockEvaluate = StockEvaluate.objects.get(stock=stock)
    else:
        stockEvaluate = StockEvaluate()
    
    stockEvaluate.stock = stock
    stockEvaluate.stock_code = stock_code

    today = datetime.strptime(date_string, "%Y%m%d")
    stockEvaluate.date = today

    if KeyValueSheetCurrent.objects.get(stock=stock)!=None:
        theStockKeySheet = KeyValueSheetCurrent.objects.get(stock=stock)
        length = allKeySheets.count()

        allKeySheets = allKeySheets.order_by('MarketValue')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.MarketValue_Score = getTheEvaluateScore(percent)
        stockEvaluate.MarketValue_Message = getTheEvaluateMessage('市值', stockEvaluate.MarketValue_Score)
        
        allKeySheets = allKeySheets.order_by('-DebtAssetRatio')
        index = list(allKeySheets).index(theStockKeySheet)
        # print(f"負載資產比 index {index}")
        percent = int((index/length)*100)
        stockEvaluate.CurrentAsset_Score = getTheEvaluateScore(percent)
        stockEvaluate.CurrentAsset_Message = getTheEvaluateMessage('負債資產比', stockEvaluate.CurrentAsset_Score)

        allKeySheets = allKeySheets.order_by('CashFlowPerShare')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.CashFlowAssetPerShare_Score = getTheEvaluateScore(percent)
        stockEvaluate.CashFlowAssetPerShare_Message = getTheEvaluateMessage('每股自由現金流', stockEvaluate.CashFlowAssetPerShare_Score)

        allKeySheets = allKeySheets.order_by('Yield')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.Yield_Score = getTheEvaluateScore(percent)
        stockEvaluate.Yield_Message = getTheEvaluateMessage('殖利率', stockEvaluate.Yield_Score)

        allKeySheets = allKeySheets.order_by('RevenueGrowthRate1Year')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.RevenueGrowth_Score = getTheEvaluateScore(percent)
        stockEvaluate.RevenueGrowth_Message = getTheEvaluateMessage('年營收成長率', stockEvaluate.RevenueGrowth_Score)

        allKeySheets = allKeySheets.order_by('EPSGrowthRate1Year')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.EPSGrowth_Score = getTheEvaluateScore(percent)
        stockEvaluate.EPSGrowth_Message = getTheEvaluateMessage('EPS年成長率 ', stockEvaluate.EPSGrowth_Score)

        allKeySheets = allKeySheets.order_by('ROEGrowthRate1Year')
        index = list(allKeySheets).index(theStockKeySheet)
        percent = int((index/length)*100)
        stockEvaluate.ROEGrowth_Score = getTheEvaluateScore(percent)
        stockEvaluate.ROEGrowth_Message = getTheEvaluateMessage('ROE年成長率 ', stockEvaluate.ROEGrowth_Score)


        stockEvaluate.Yearly_Divident_Score = checkTheDividentScore(stock, today)
        stockEvaluate.Yearly_Divident_Message = getTheDividentMessage(stockEvaluate.Yearly_Divident_Score)
    
    #以下算折現法,目前有錯
    seasonSheets = KeyValueSheetSeason.objects.filter(stock=stock, date__range=[f"{today.year-5}-01-01", f"{today.year-1}-12-31"]).order_by('-date')
    if seasonSheets.count()>16 and seasonSheets.count() <= 20:
        divide_num = 5
    elif seasonSheets.count()>12 and seasonSheets.count() <= 16:
        divide_num = 4
    elif seasonSheets.count()>8 and seasonSheets.count() <= 12:
        divide_num = 3
    elif seasonSheets.count()>4 and seasonSheets.count() <= 8:
        divide_num = 2
    elif seasonSheets.count()>0 and seasonSheets.count() <= 4:
        divide_num = 1
    else:
        divide_num = 1

    yearPERatioArray = []
    i = 1
    while i<=5:
        eps = 0
        yearSeasonSheets = KeyValueSheetSeason.objects.filter(stock=stock, date__range=[f"{today.year-i}-01-01", f"{today.year-i}-12-31"])
        for sheet in yearSeasonSheets:
            eps = eps + sheet.EPS
        try:
            yearPERatio = yearSeasonSheets.last().ReferenceStockPrice / eps  
        except:
            yearPERatio = 0
        yearPERatioArray.append(yearPERatio)
        i = i + 1

    if divide_num != None:
        #這裡這樣會算錯
        avgROE = sum(seasonSheet.ReturnOfEquity for seasonSheet in seasonSheets) / divide_num / 100
        
        totalEPS = sum(seasonSheet.EPS for seasonSheet in seasonSheets)
        totalDividend = sum(seasonSheet.EPS for seasonSheet in seasonSheets)
        try:
            avgPayoutRatio = totalDividend/totalDividend
        except:
            avgPayoutRatio = 0

        avgPERatio = sum(yearPERatioArray) / divide_num

        try:
            initialBookPrice = seasonSheets[0].ReferenceStockPrice / seasonSheets[0].PriceBookRatio
        except:
            initialBookPrice = 0
        
        discountArray = [1, 1.05, 1.1, 1.15]

        priceArray = []
        epsArray = []
        bookPriceArray = []
        dividendArray = []
        for discount in discountArray:

            epsArray.append( initialBookPrice* avgROE)
            bookPriceArray.append(initialBookPrice)
            dividendArray.append(initialBookPrice * avgROE * avgPayoutRatio)
            # 假設持有5年

            for i in range(4):
                newBookPrice = epsArray[i] * (1-avgPayoutRatio) + bookPriceArray[i]
                bookPriceArray.append(newBookPrice)

                newEPS = newBookPrice * avgROE
                epsArray.append(newEPS)

                newdividend = newEPS * avgPayoutRatio
                dividendArray.append(newdividend)

            price = 0
            for i in range(5):
                price = price + float(dividendArray[i]) / discount**(i+1) 
            price = price + float(epsArray[4]) * float(avgPERatio) / discount ** 5
            priceArray.append(price)

        stockEvaluate.DividentDicount_0DiscountRate = priceArray[0]
        stockEvaluate.DividentDicount_5DiscountRate = priceArray[1]
        stockEvaluate.DividentDicount_10DiscountRate = priceArray[2]
        stockEvaluate.DividentDicount_15DiscountRate = priceArray[3]

        priceArray = []
        epsArray = []
        avgEPS = totalEPS / divide_num

        try:
            avgEPSGrowthRate = sum(seasonSheet.EPSGrowthRate1Year for seasonSheet in seasonSheets) / len(seasonSheets) / 100
        except:
            avgEPSGrowthRate = 0

        for discount in discountArray:
            epsArray.append(avgEPS)
            for i in range(4):
                epsArray.append( epsArray[i] + epsArray[i]*avgEPSGrowthRate )

            price = 0
            for i in range(5):
                price = price + float(epsArray[i]) / discount**(i+1)
            price = price + float(epsArray[4]) * float(avgPERatio) / discount**5
            priceArray.append(price)

        stockEvaluate.CashFlowDiscount_0DiscountRate = priceArray[0]
        stockEvaluate.CashFlowDiscount_5DiscountRate = priceArray[1]
        stockEvaluate.CashFlowDiscount_10DiscountRate = priceArray[2]
        stockEvaluate.CashFlowDiscount_15DiscountRate = priceArray[3]
        
        recentStockPrice = StockRecord.objects.filter(stock=stock).order_by('-date')[0].ClosingPrice

        if recentStockPrice < stockEvaluate.DividentDicount_15DiscountRate :
            stockEvaluate.Divident_Evaluate_Score = 10
            stockEvaluate.Divident_Evaluate_Message = '股價 < 股利折現法估價的 15% 折現率內'
        elif recentStockPrice < stockEvaluate.DividentDicount_10DiscountRate :
            stockEvaluate.Divident_Evaluate_Score = 7
            stockEvaluate.Divident_Evaluate_Message = '股價 < 股利折現法估價的 10% 折現率內'
        elif recentStockPrice < stockEvaluate.DividentDicount_5DiscountRate :
            stockEvaluate.Divident_Evaluate_Score = 5
            stockEvaluate.Divident_Evaluate_Message = '股價 < 股利折現法估價的 5% 折現率內'
        elif recentStockPrice < stockEvaluate.DividentDicount_0DiscountRate :
            stockEvaluate.Divident_Evaluate_Score = 3
            stockEvaluate.Divident_Evaluate_Message = '股價 < 股利折現法估價的 0% 折現率內'
        else:
            stockEvaluate.Divident_Evaluate_Score = 0
            stockEvaluate.Divident_Evaluate_Message = '股價 < 股利折現法估價的任何估算'
        
        if recentStockPrice < stockEvaluate.CashFlowDiscount_15DiscountRate :
            stockEvaluate.CashFlow_Evaluate_Score = 10
            stockEvaluate.CashFlow_Evaluate_Message = '股價 < 現金折現法估價的 15% 折現率內'
        elif recentStockPrice < stockEvaluate.CashFlowDiscount_10DiscountRate :
            stockEvaluate.CashFlow_Evaluate_Score = 7
            stockEvaluate.CashFlow_Evaluate_Message = '股價 < 現金折現法估價的 10% 折現率內'
        elif recentStockPrice < stockEvaluate.CashFlowDiscount_5DiscountRate :
            stockEvaluate.CashFlow_Evaluate_Score = 5
            stockEvaluate.CashFlow_Evaluate_Message = '股價 < 現金折現法估價的 5% 折現率內'
        elif recentStockPrice < stockEvaluate.CashFlowDiscount_0DiscountRate :
            stockEvaluate.CashFlow_Evaluate_Score = 3
            stockEvaluate.CashFlow_Evaluate_Message = '股價 < 現金折現法估價的 0% 折現率內'
        else:
            stockEvaluate.CashFlow_Evaluate_Score = 0
            stockEvaluate.CashFlow_Evaluate_Message = '股價 < 現金折現法估價的任何估算'
    
    stockEvaluate.total_score = stockEvaluate.MarketValue_Score + stockEvaluate.CurrentAsset_Score + stockEvaluate.CashFlowAssetPerShare_Score  \
                                + stockEvaluate.Yield_Score + stockEvaluate.Yearly_Divident_Score \
                                + stockEvaluate.RevenueGrowth_Score + stockEvaluate.EPSGrowth_Score + stockEvaluate.ROEGrowth_Score + \
                                stockEvaluate.Divident_Evaluate_Score + stockEvaluate.CashFlow_Evaluate_Score 

    print(
        str(stockEvaluate.DividentDicount_0DiscountRate) + " " +
        str(stockEvaluate.DividentDicount_5DiscountRate) + " " +
        str(stockEvaluate.DividentDicount_10DiscountRate) + " " +
        str(stockEvaluate.DividentDicount_15DiscountRate) + " " +
        str(stockEvaluate.CashFlowDiscount_0DiscountRate) + " " +
        str(stockEvaluate.CashFlowDiscount_5DiscountRate) + " " +
        str(stockEvaluate.CashFlowDiscount_10DiscountRate) + " " +
        str(stockEvaluate.CashFlowDiscount_15DiscountRate) + " " +
        str(stockEvaluate.MarketValue_Score) + " " +
        str(stockEvaluate.CurrentAsset_Score) + " " +
        str(stockEvaluate.CashFlowAssetPerShare_Score) + " " +
        str(stockEvaluate.Yield_Score) + " " +
        str(stockEvaluate.Yearly_Divident_Score) + " " +
        str(stockEvaluate.RevenueGrowth_Score) + " " +
        str(stockEvaluate.EPSGrowth_Score) + " " +
        str(stockEvaluate.ROEGrowth_Score) + " " +
        str(stockEvaluate.Divident_Evaluate_Score) + " " +
        str(stockEvaluate.CashFlow_Evaluate_Score) + " " )


    stockEvaluate.save()

def getTheEvaluateScore(percent):
    if percent>=90 and percent <= 100:
        return 10
    elif percent>=80 and percent < 90:
        return 9
    elif percent>=70 and percent < 80:
        return 8
    elif percent>=60 and percent < 70:
        return 7
    elif percent>=50 and percent < 60:
        return 6
    elif percent>=40 and percent < 50:
        return 5
    elif percent>=30 and percent < 40:
        return 4
    elif percent>=20 and percent < 30:
        return 3
    elif percent>=10 and percent < 20:
        return 2
    elif percent>=0 and percent < 10:
        return 1

def getTheEvaluateMessage(keyString, score):
    return f'{keyString} 在上市櫃中排序為 { (score-1)*10 }%~{ (score)*10 }%'

def checkTheDividentScore(stock, today):
    score = 0
    for i in range(1,6):
        if DividendSheet.objects.filter(date__range=[f"{today.year-i}-01-01", f"{today.year-i}-12-31"]).count() != 0:
            score = score + 2
    return score

def getTheDividentMessage(score):
    return f"近 5 年 有 {score/2} 年正常發放股利息"

# this method is on the model's manager
def get_closest_to(self, target):
    closest_greater_qs = self.filter(date__gt=target).order_by('date')
    closest_less_qs    = self.filter(date__lt=target).order_by('-date')

    try:
        try:
            closest_greater = closest_greater_qs[0]
        except IndexError:
            return closest_less_qs[0]

        try:
            closest_less = closest_less_qs[0]
        except IndexError:
            return closest_greater_qs[0]
    except IndexError:
        raise self.model.DoesNotExist("There is no closest object"
                                      " because there are no objects.")

    if closest_greater.date - target > target - closest_less.date:
        return closest_less
    else:
        return closest_greater