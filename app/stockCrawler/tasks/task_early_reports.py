from stockCore.models import Stock, RevenueSheet, Category, DividendSheet, CashFlowStatement, IncomeStatement, BalanceSheet, StockRecord
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
from celery import shared_task

#this task file crawl early financial report from 96年Q2~102年Q4
#20070630~20120331

def crawl_all_stocks_early_sheets():
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.category != Category.objects.get(id=26) and stock.category != Category.objects.get(id=29) and stock.category != Category.objects.get(id=32) and stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':
            
            startDate = datetime(2007,6,30)
            end_date = datetime(2012,12,31)

            if StockRecord.objects.filter(stock=stock).count() != 0 and StockRecord.objects.filter(stock=stock).order_by('date')[0].date > startDate.date():
                newDate = StockRecord.objects.filter(stock=stock).order_by('date')[0].date
                if newDate.month <= 3:
                    startDate = datetime(newDate.year,3,31)
                elif newDate.month >= 4 and newDate.month <= 6:
                    startDate = datetime(newDate.year,6,30)
                elif newDate.month >= 7 and newDate.month <= 9:
                    startDate = datetime(newDate.year,9,30)
                elif newDate.month >= 10 and newDate.month <= 12:
                    startDate = datetime(newDate.year,12,31)
            
            while startDate <= end_date:
                date_string = startDate.strftime("%Y%m%d")
                if BalanceSheet.objects.filter(stock=stock, date=startDate).count() == 0:
                    crawl_early_balance_sheet_by_date.delay(stock.stock_code, date_string)
                if IncomeStatement.objects.filter(stock=stock, date=startDate).count() == 0:
                    crawl_early_income_sheet_by_date.delay(stock.stock_code, date_string)
                # if startDate>=datetime(2010,12,31) and CashFlowStatement.objects.filter(stock=stock, date=startDate).count() == 0:
                if startDate>=datetime(2010,12,31):
                    crawl_early_cash_flow_statement.delay(stock.stock_code, date_string)

                if startDate.month == 3:
                    startDate = datetime(startDate.year,6,30)
                elif startDate.month == 6:
                    startDate = datetime(startDate.year,9,30)
                elif startDate.month == 9:
                    startDate = datetime(startDate.year,12,31)
                elif startDate.month == 12:
                    startDate = datetime(startDate.year+1,3,31)

def calculate_season_key_value():
    from stockCrawler.tasks.tasks import calculate_season_key_values

    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.category != Category.objects.get(id=26) and stock.category != Category.objects.get(id=29) and stock.category != Category.objects.get(id=32) and stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':
            
            startDate = datetime(2010,12,31)
            end_date = datetime(2021,9,30)
            
            while startDate <= end_date:
                date_string = startDate.strftime("%Y%m%d")
                if BalanceSheet.objects.filter(stock=stock, date=startDate).count() != 0:
                    calculate_season_key_values(stock.stock_code, date_string)
                
                if startDate.month == 3:
                    startDate = datetime(startDate.year,6,30)
                elif startDate.month == 6:
                    startDate = datetime(startDate.year,9,30)
                elif startDate.month == 9:
                    startDate = datetime(startDate.year,12,31)
                elif startDate.month == 12:
                    startDate = datetime(startDate.year+1,3,31)

@shared_task
def crawl_early_balance_sheet_by_date(stock_code ,date_string):
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

    url = f'https://mops.twse.com.tw/mops/web/ajax_t05st33?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)
    
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    soup = BeautifulSoup(resp.text, 'html.parser')

    try:
        tables = soup.find_all('table')
        table = tables[2]
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
                item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','').replace('.00','')
                # print(item_title + item_content)
                if '現金及約當現金' in item_title:
                    # print(item_title)
                    currentAssets_Cash = item_content
                elif ('公平價值變動列入損益之金融資產-流動' in item_title) or ('備供出售金融資產-流動' in item_title) or (' 持有至到期日金融資產-流動' in item_title) or ('其他金融資產-流動' in item_title):
                    # print(item_title)
                    currentAssets_FinancialSubTotal =  currentAssets_FinancialSubTotal + int(item_content)
                elif ('應收帳款淨額' in item_title) or ('應收帳款–關係人淨額' in item_title) or ('其他應收款–關係人' in item_title):
                    # print(item_title)
                    currentAssets_AccountReceivableSubTotal =  currentAssets_AccountReceivableSubTotal + int(item_content)
                elif '存貨' in item_title:
                    # print(item_title + item_content)
                    currentAssets_Inventory =  item_content
                elif '其他流動資產' in item_title:
                    # print(item_title)
                    currentAssets_Others =  item_content
                elif ('流動資產' in item_title) and ('其他流動資產' not in item_title) and (item_content != ''):
                    # print(item_title)
                    currentAssets_Total =  item_content
                elif ('基金及投資' in item_title) and (item_content != ''):
                    # print(item_title)
                    nonCurrentAssets_FinancialSubTotoal =  int(item_content)
                elif ('固定資產淨額' in item_title) and (item_content != ''):
                    # print(item_title)
                    nonCurrentAssets_RealEstate = item_content
                elif '其他非流動資產' in item_title:
                    # print(item_title)
                    nonCurrentAssets_Others =  item_content
                elif ('無形資產合計' in item_title) or ('其他資產合計' in item_title):
                    # print(item_title)
                    nonCurrentAssets_Total =  nonCurrentAssets_Total + int(item_content)
                elif '資產總額' in item_title or '資產總計' in item_title:
                    # print(item_title)
                    assetTotal =  item_content
                elif '短期借款' in item_title:
                    # print(item_title)
                    currentDebt_Cash =  item_content
                elif '公平價值變動列入損益之金融負債-流動' in item_title or '避險之衍生性金融負債-流動' in item_title:
                    # print(item_title)
                    currentDebt_FinancialSubTotal =  currentDebt_FinancialSubTotal + int(item_content)
                elif '應付帳款' == item_title or '應付帳款–關係人' == item_title or '應付所得稅' in item_title or '應付費用' in item_title or '其他應付款項' in item_title:
                    # print(item_title)
                    currentDebt_AccountReceivableSubTotal =  currentDebt_AccountReceivableSubTotal + int(item_content)
                elif '一年或一營業週期內到期長期負債' in item_title:
                    # print(item_title)
                    currentDebt_Others =  item_content
                elif '流動負債' in item_title and (item_content != ''):
                    # print(item_title)
                    currentDebt_Total =  item_content
                elif '應付公司債' in item_title:
                    # print(item_title)
                    nonCurrentDebt_CompanyBond =  item_content
                elif '長期借款' in item_title:
                    # print(item_title)
                    nonCurrentDebt_LongTermLoan =  item_content
                elif '其他負債合計' in item_title:
                    # print(item_title)
                    nonCurrentDebt_Others =  item_content
                elif '非流動負債合計' in item_title:
                    # print(item_title + item_content)
                    nonCurrentDebt_Total =  item_content
                elif '負債總額' in item_title or '負債總計' in item_title:
                    # print(item_title)
                    debtTotal =  item_content
                elif '普通股股本' in item_title:
                    # print(item_title)
                    equity_CommonStock =  item_content
                elif '資本公積合計' in item_title:
                    # print(item_title)
                    equity_CapitalReserve =  item_content
                elif '保留盈餘合計' in item_title:
                    # print(item_title)
                    equity_RetainedEarnings =  item_content
                elif '股東權益其他調整項目合計' in item_title:
                    # print(item_title)
                    equity_Others =  item_content
                elif '少數股權' in item_title:
                    # print(item_title)
                    equity_NonControllingInterests =  item_content
                elif '股東權益總計' in item_title:
                    # print(item_title)
                    equity_Total =  item_content
                    # print(equity_Total)
            except:
                print('this tr no content')

        print("股本 " + equity_CommonStock)
        print("權益"  + equity_Total)
        equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
        print(f'淨值 {equity_Per_Share}')

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

    except:
        print("data error!")

@shared_task
def crawl_early_income_sheet_by_date(stock_code, date_string):
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

    url = f'https://mops.twse.com.tw/mops/web/ajax_t05st34?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&&season={season}'
    # url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')

    try:
        tables = soup.find_all('table')
        table = tables[3]
        trs = table.find_all('tr')
        
        revenue = 0
        cost = 0
        gross = 0
        promotionExpense = 0
        manageExpense = 0
        researchExpense = 0
        totalExpense = 0

        operatingProfit = 0
        profitBeforeTax = 0
        profitAfterTax = 0

        otherIncome = 0
        totalIncome = 0

        parentProfit = 0
        childProfit = 0
        ePS_Period = 0

        for item in trs:
            try:
                item_title = item.find_all('td')[0].getText().replace(' ','')
                item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
                if '營業收入合計' in item_title:
                    revenue = item_content
                elif '營業成本合計' in item_title:
                    cost =  item_content
                elif '營業毛利(毛損)' in item_title:
                    gross =  item_content
                elif '推銷費用' in item_title:
                    promotionExpense =  item_content
                elif '管理及總務費用' in item_title:
                    manageExpense =  item_content
                elif '研究發展費用' in item_title:
                    researchExpense =  item_content
                elif '營業費用合計' in item_title:
                    totalExpense =  item_content
                elif '營業淨利(淨損)' in item_title:
                    operatingProfit =  item_content

                elif '營業外收入及利益' in item_title and item_content != '':
                    otherIncome =  item_content

                elif '繼續營業單位稅前淨利(淨損)' in item_title:
                    profitBeforeTax =  item_content
                elif '繼續營業單位淨利(淨損)' in item_title:
                    profitAfterTax =  item_content

                elif '合併淨損益' in item_title:
                    parentProfit =  item_content
                elif '少數股權損益' in item_title:
                    childProfit =  item_content
                elif '合併總損益' in item_title:
                    totalIncome =  item_content

                elif '基本每股盈餘' in item_title and item_content != '':
                    ePS_Period =  item_content
            except:
                print('this tr no content')

        if IncomeStatement.objects.filter(stock=stock, date=startDate).count() == 0:
            stateMent = IncomeStatement()
        else:
            stateMent = IncomeStatement.objects.get(stock=stock, date=startDate)

        stateMent.stock_code = stock_code
        stateMent.stock = stock
        stateMent.date = startDate
        stateMent.Revenue = revenue
        stateMent.Cost = cost
        stateMent.Gross = gross
        stateMent.PromotionExpense = promotionExpense
        stateMent.ManageExpense = manageExpense
        stateMent.ResearchExpense = researchExpense
        stateMent.TotalExpense = totalExpense
        stateMent.OperatingProfit = operatingProfit
        stateMent.ProfitBeforeTax = profitBeforeTax
        stateMent.ProfitAfterTax = profitAfterTax
        stateMent.OtherIncome = otherIncome
        stateMent.TotalIncome = totalIncome
        stateMent.ParentProfit = parentProfit
        stateMent.ChildProfit = childProfit
        stateMent.EPS_Period = ePS_Period
        stateMent.save()
    except:
        print("data error!")

@shared_task
def crawl_early_cash_flow_statement(stock_code, date_string):
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
    
    url = f'https://mops.twse.com.tw/mops/web/ajax_t05st39?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    # url = f'https://mops.twse.com.tw/mops/web/t164sb05?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)
    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)
    
    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')

    try:
        tables = soup.find_all('table')
        table = tables[3]
        lines = str(tables[3]).split('\n')

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

        IncomeTax = 0
        PlantEquipment = 0
        ExchangeRateImpact = 0

        for item in lines:
            # print(item)
            try:
                elements = item.split()
                # print(elements)
                item_title = elements[0].replace(' ','')
                item_content = elements[1].replace(' ','').replace(',','').replace('$','')

                if('(' in item_content and ')' in item_content):
                    item_content = item_content.replace('(','').replace(')','')
                    item_content = '-'+item_content
                
                # print(item_title + item_content)

                if '合併總(損)益' in item_title:
                    revenueBeforeTax = item_content
                elif '折舊費用' in item_title:
                    depreciation =  item_content
                elif '攤銷費用' in item_title:
                    amortization =  item_content

                # elif '利息收入' in item_title:
                #     interestIncome =  item_content
                # elif '股利收入' in item_title:
                #     dividendExpenditure =  item_content
                # elif '收益費損項目合計' in item_title:
                #     incomeChargesNotAffectingCash =  item_content
                # elif '營業活動相關之資產及負債之淨變動' in item_title:
                #     assetsDebtsIncome =  item_content

                elif '營業活動之淨現金流入(流出)' in item_title:
                    operatingCashFlow =  item_content

                elif '購置固定資產' in item_title:
                    PlantEquipment =  item_content
                elif '投資活動之淨現金流入(流出)' in item_title:
                    investingCashFlow =  item_content

                elif '融資活動之淨現金流入(流出)' in item_title:
                    financingCashFlow =  item_content

                elif '匯率影響數' in item_title:
                    ExchangeRateImpact =  item_content
                elif '支付所得稅' in item_title:
                    IncomeTax =  item_content

                elif '本期現金及約當現金淨增減數' in item_title:
                    netCashFlow =  item_content
                elif '期末現金及約當現金餘額' in item_title:
                    totalAssetsCash =  item_content
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

        stateMent.IncomeTax = IncomeTax
        stateMent.PlantEquipment = PlantEquipment
        stateMent.ExchangeRateImpact = ExchangeRateImpact

        stateMent.save()
    except:
        print('data error!')