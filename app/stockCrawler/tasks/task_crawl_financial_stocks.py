from celery import shared_task
import requests
from bs4 import BeautifulSoup
from stockCore.models import Stock, BalanceSheet, IncomeStatement, CashFlowStatement, StockRecord, KeyValueSheetSeason, KeyValueSheetCurrent, StockEvaluate
from datetime import date, datetime
from django.db.models import Q


def crawl_financial_stocks_first_set():
    stocks = Stock.objects.filter(Q(category=26) | Q(category=32))
    banck_codes = '5880, 5876, 2897, 2892, 2891, 2890, 2889, 2888, 2887, 2886, 2885, 2884, 2883, 2882, 2881, 2880, 2849, 2845, 2838, 2836, 2834, 2812, 2809, 2801'
    insurance_codes = '2867, 2852, 2851, 2850, 2832, 2823, 2816'
    securities_codes = '5864, 6026, 5878, 6023, 6021, 6020, 6016, 6015, 5820, 6024, 6005, 2855, 2820'

    for stock in stocks:

        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':
            #set start_date
            
            startDate = datetime(2013,3,31)

            if StockRecord.objects.filter(stock=stock).order_by('date')[0].date > startDate.date():
                newDate = StockRecord.objects.filter(stock=stock).order_by('date')[0].date
                if newDate.month <= 3:
                    startDate = datetime(newDate.year,3,31)
                elif newDate.month >= 4 and newDate.month <= 6:
                    startDate = datetime(newDate.year,6,30)
                elif newDate.month >= 7 and newDate.month <= 9:
                    startDate = datetime(newDate.year,9,30)
                elif newDate.month >= 10 and newDate.month <= 12:
                    startDate = datetime(newDate.year,12,31)
                
            end_date = datetime(2021,9,30)

            while startDate <= end_date:
                date_string = startDate.strftime("%Y%m%d")
                if(stock.stock_code in banck_codes):
                    crawl_bank_balance_sheet.delay(stock.stock_code, date_string)
                    crawl_bank_income_sheet.delay(stock.stock_code, date_string)
                    crawl_bank_cash_flow_statement.delay(stock.stock_code, date_string)
                elif(stock.stock_code in insurance_codes):
                    crawl_insurance_balance_sheet.delay(stock.stock_code, date_string)
                    crawl_insurance_income_sheet.delay(stock.stock_code, date_string)
                    crawl_bank_cash_flow_statement.delay(stock.stock_code, date_string)
                elif(stock.stock_code in securities_codes):
                    crawl_securities_balance_sheet.delay(stock.stock_code, date_string)
                    crawl_securities_income_sheet.delay(stock.stock_code, date_string)
                    crawl_bank_cash_flow_statement.delay(stock.stock_code, date_string)

                if startDate.month == 3:
                    startDate = datetime(startDate.year,6,30)
                elif startDate.month == 6:
                    startDate = datetime(startDate.year,9,30)
                elif startDate.month == 9:
                    startDate = datetime(startDate.year,12,31)
                elif startDate.month == 12:
                    startDate = datetime(startDate.year+1,3,31)

def calculate_financial_stocks_season_key_values():
    from stockCrawler.tasks.tasks import calculate_season_key_values
    stocks = Stock.objects.filter(Q(category=26) | Q(category=32))

    for stock in stocks:
        sheets = BalanceSheet.objects.filter(stock=stock).order_by('date')
        for sheet in sheets:
            date_string = sheet.date.strftime("%Y%m%d")
            calculate_season_key_values(stock.stock_code, date_string)

def calculate_financial_stocks_current_key_value():
    from stockCrawler.tasks.tasks import calculate_current_key_values
    stocks = Stock.objects.filter(Q(category=26) | Q(category=32))
    
    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and KeyValueSheetSeason.objects.filter(stock=stock).count() != 0:
            calculate_current_key_values(stock.stock_code)

def calcuate_financial_stocks_evalutate():
    from stockCrawler.tasks.tasks import calculate_stock_evalutate
    stocks = Stock.objects.filter(Q(category=26) | Q(category=32))

    for stock in stocks:
        if KeyValueSheetCurrent.objects.filter(stock=stock).count() != 0:
            calculate_stock_evalutate(stock.stock_code, '20220118')
        elif StockEvaluate.objects.filter(stock=stock).count() != 0:
            StockEvaluate.objects.filter(stock=stock).delete()

# bank stock codes = 5880, 5876, 2897, 2892, 2891, 2890, 2889, 2888, 2887, 2886, 2885, 2884, 2883, 2882, 2881, 2880, 2849, 2845, 2838, 2836, 2834, 2812, 2809, 2801
@shared_task
def crawl_bank_balance_sheet(stock_code, date_string):

    startDate = datetime.strptime(date_string, '%Y%m%d')

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'
    
    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
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
    currentAssets_Total = 0

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
            elif ('應收款項－淨額' in item_title):
                # print(item_title)
                currentAssets_AccountReceivableSubTotal =  int(item_content)
            elif '其他金融資產－淨額' in item_title:
                # print(item_title)
                currentAssets_Others =  item_content
            elif ('投資性不動產－淨額' in item_title):
                # print(item_title)
                nonCurrentAssets_FinancialSubTotoal =  int(item_content)
            elif '不動產及設備－淨額' in item_title:
                # print(item_title)
                nonCurrentAssets_RealEstate = item_content
            elif '其他資產－淨額' in item_title:
                # print(item_title)
                nonCurrentAssets_Others =  item_content
            elif '資產總計' in item_title or '資產總額' in item_title:
                # print(item_title)
                assetTotal =  item_content
            elif '應付款項' in item_title:
                # print(item_title)
                currentDebt_FinancialSubTotal =  int(item_content)
            elif '其他金融負債' in item_title:
                # print(item_title)
                nonCurrentDebt_Others =  item_content
            elif '負債總計' in item_title or '負債總額' in item_title:
                # print(item_title)
                debtTotal =  item_content
            elif '股本' == item_title or '股本合計' == item_title:
                # print(item_title)
                equity_CommonStock =  item_content
                # print(equity_CommonStock)
            elif '資本公積' == item_title:
                # print(item_title)
                equity_CapitalReserve =  item_content
            elif '保留盈餘' in item_title:
                # print(item_title)
                equity_RetainedEarnings =  item_content
            elif '其他權益' in item_title:
                # print(item_title)
                equity_Others =  item_content
            elif '非控制權益' in item_title:
                # print(item_title)
                equity_NonControllingInterests =  item_content
            elif '權益總計' == item_title  or '權益總額' in item_title:
                # print(item_title)
                equity_Total =  item_content
        except:
            print('this tr no content')

    print("股本 " + str(equity_CommonStock))
    print("資產 " + str(assetTotal))
    print("權益總計 " + str(equity_Total))
    equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
    print("每股淨值 " + str(equity_Per_Share))

    stock = Stock.objects.get(stock_code=stock_code)

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

    crawl_bank_share_holder(stock.stock_code, date_string)

############### crawl_share_hodlder are all the same
@shared_task
def crawl_bank_share_holder(stock_code, date_string):
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

@shared_task
def crawl_bank_income_sheet(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'

    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table',{'class':'hasBorder'})
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
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '淨收益' == item_title:
                print(item_title)
                revenue = item_content
            elif '營業費用' == item_title or '營業費用合計' == item_title:
                print(item_title)
                totalExpense =  item_content
            elif '繼續營業單位稅前損益' in item_title or '繼續營業單位稅前淨利' in item_title:
                print(item_title)
                profitBeforeTax =  item_content
            elif '本期稅後淨利' in item_title and item_content != '':
                print(item_title)
                profitAfterTax =  item_content
            elif '本期其他綜合損益（稅後淨額）' in item_title and item_content != '':
                print(item_title)
                otherIncome =  item_content
            elif '本期綜合損益總額' in item_title:
                print(item_title)
                totalIncome =  item_content
            elif '母公司業主（綜合損益）' in item_title:
                print(item_title)
                parentProfit =  item_content
            elif '非控制權益（綜合損益）' in item_title:
                print(item_title)
                childProfit =  item_content
            elif '　基本每股盈餘' == item_title and item_content != '':
                print(item_title)
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
    
    if season == "4":
        statement = IncomeStatement.objects.get(stock=stock, date=startDate)
        start_date = f'{statement.date.year}-01-01'
        end_date = f'{statement.date.year}-10-01'
        statements_before_this_season_of_the_year = IncomeStatement.objects.filter(stock=stock, date__gte = start_date, date__lte = end_date)
        for season_state in statements_before_this_season_of_the_year:

            statement.Revenue = statement.Revenue - season_state.Revenue
            statement.Cost = statement.Cost - season_state.Cost
            statement.Gross = statement.Gross - season_state.Gross

            statement.PromotionExpense = statement.PromotionExpense - season_state.PromotionExpense
            statement.ManageExpense = statement.ManageExpense - season_state.ManageExpense
            statement.ResearchExpense = statement.ResearchExpense - season_state.ResearchExpense
            statement.TotalExpense = statement.TotalExpense - season_state.TotalExpense

            statement.OperatingProfit = statement.OperatingProfit - season_state.OperatingProfit
            statement.ProfitBeforeTax = statement.ProfitBeforeTax - season_state.ProfitBeforeTax
            statement.ProfitAfterTax = statement.ProfitAfterTax - season_state.ProfitAfterTax
            statement.OtherIncome = statement.OtherIncome - season_state.OtherIncome
            statement.TotalIncome = statement.TotalIncome - season_state.TotalIncome

            statement.ParentProfit = statement.ParentProfit - season_state.ParentProfit
            statement.ChildProfit = statement.ChildProfit - season_state.ChildProfit
            statement.EPS_Period = statement.EPS_Period - season_state.EPS_Period

            statement.save()

############### crawl_cash_flow are all the same
@shared_task
def crawl_bank_cash_flow_statement(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)
        
    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'

    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb05?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb05?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb05?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
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

    for item in trs:
        try:
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '本期稅前淨利' in item_title:
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
    stateMent.save()

# insurance stock codes = 2867, 2852, 2851, 2850, 2832, 2823, 2816
@shared_task
def crawl_insurance_balance_sheet(stock_code, date_string):

    startDate = datetime.strptime(date_string, '%Y%m%d')

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'
    
    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
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
    currentAssets_Total = 0

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
            elif ('應收款項－淨額' in item_title):
                # print(item_title)
                currentAssets_AccountReceivableSubTotal =  int(item_content)
            elif '其他金融資產－淨額' in item_title:
                # print(item_title)
                currentAssets_Others =  item_content
            elif ('投資性不動產－淨額' in item_title):
                # print(item_title)
                nonCurrentAssets_FinancialSubTotoal =  int(item_content)
            elif '不動產及設備－淨額' in item_title:
                # print(item_title)
                nonCurrentAssets_RealEstate = item_content
            elif '其他資產－淨額' in item_title:
                # print(item_title)
                nonCurrentAssets_Others =  item_content
            elif '資產總計' in item_title:
                # print(item_title)
                assetTotal =  item_content
            elif '應付款項' in item_title:
                # print(item_title)
                currentDebt_FinancialSubTotal =  int(item_content)
            elif '其他金融負債' in item_title:
                # print(item_title)
                nonCurrentDebt_Others =  item_content
            elif '負債總計' in item_title:
                # print(item_title)
                debtTotal =  item_content
            elif '股本合計' in item_title:
                # print(item_title)
                equity_CommonStock =  item_content
                # print(equity_CommonStock)
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
            elif '權益總計' == item_title:
                # print(item_title)
                equity_Total =  item_content
        except:
            print('this tr no content')

    print("股本 " + str(equity_CommonStock))
    print("資產 " + str(assetTotal))
    print("權益總計 " + str(equity_Total))
    equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
    print("每股淨值 " + str(equity_Per_Share))

    stock = Stock.objects.get(stock_code=stock_code)

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

@shared_task
def crawl_insurance_income_sheet(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'

    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table',{'class':'hasBorder'})
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
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '營業收入合計' == item_title:
                print(item_title)
                revenue = item_content
            elif '營業成本合計' == item_title:
                print(item_title)
                cost = item_content
            elif '營業費用合計' == item_title:
                print(item_title)
                totalExpense =  item_content
            elif '繼續營業單位稅前純益' in item_title:
                print(item_title)
                profitBeforeTax =  item_content
            elif '本期淨利' in item_title:
                print(item_title)
                profitAfterTax =  item_content
            elif '其他綜合損益（稅後淨額）' in item_title and item_content != '':
                print(item_title)
                otherIncome =  item_content
            elif '本期綜合損益總額	' in item_title:
                print(item_title)
                totalIncome =  item_content
            elif '基本每股盈餘' in item_title and item_content != '':
                print(item_title)
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
    
    if season == "4":
        statement = IncomeStatement.objects.get(stock=stock, date=startDate)
        start_date = f'{statement.date.year}-01-01'
        end_date = f'{statement.date.year}-10-01'
        statements_before_this_season_of_the_year = IncomeStatement.objects.filter(stock=stock, date__gte = start_date, date__lte = end_date)
        for season_state in statements_before_this_season_of_the_year:

            statement.Revenue = statement.Revenue - season_state.Revenue
            statement.Cost = statement.Cost - season_state.Cost
            statement.Gross = statement.Gross - season_state.Gross

            statement.PromotionExpense = statement.PromotionExpense - season_state.PromotionExpense
            statement.ManageExpense = statement.ManageExpense - season_state.ManageExpense
            statement.ResearchExpense = statement.ResearchExpense - season_state.ResearchExpense
            statement.TotalExpense = statement.TotalExpense - season_state.TotalExpense

            statement.OperatingProfit = statement.OperatingProfit - season_state.OperatingProfit
            statement.ProfitBeforeTax = statement.ProfitBeforeTax - season_state.ProfitBeforeTax
            statement.ProfitAfterTax = statement.ProfitAfterTax - season_state.ProfitAfterTax
            statement.OtherIncome = statement.OtherIncome - season_state.OtherIncome
            statement.TotalIncome = statement.TotalIncome - season_state.TotalIncome

            statement.ParentProfit = statement.ParentProfit - season_state.ParentProfit
            statement.ChildProfit = statement.ChildProfit - season_state.ChildProfit
            statement.EPS_Period = statement.EPS_Period - season_state.EPS_Period

            statement.save()

# securities stock codes = 5864, 6026, 5878, 6023, 6021, 6020, 6016, 6015, 5820, 6024, 6005, 2855, 2820
@shared_task
def crawl_securities_balance_sheet(stock_code, date_string):

    startDate = datetime.strptime(date_string, '%Y%m%d')

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'
    
    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb03?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
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
    currentAssets_Total = 0

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
            elif '應收帳款' in item_title:
                # print(item_title)
                currentAssets_AccountReceivableSubTotal =  int(item_content)
            elif '其他流動資產' in item_title:
                # print(item_title)
                currentAssets_Others =  item_content
            elif '流動資產合計' in item_title:
                # print(item_title)
                currentAssets_Total =  item_content
            elif ('透過其他綜合損益按公允價值衡量之金融資產-非流動' in item_title):
                # print(item_title)
                nonCurrentAssets_FinancialSubTotoal =  int(item_content)
            elif '不動產及設備合計' in item_title:
                # print(item_title)
                nonCurrentAssets_RealEstate = item_content
            elif '其他非流動資產合計' in item_title:
                # print(item_title)
                nonCurrentAssets_Others =  item_content
            elif '資產總計' in item_title:
                # print(item_title)
                assetTotal =  item_content
            elif '應付款項' in item_title:
                # print(item_title)
                currentDebt_FinancialSubTotal =  int(item_content)
            elif '流動負債合計' in item_title:
                # print(item_title)
                currentDebt_Total =  item_content
            elif '非流動負債合計' in item_title:
                # print(item_title + item_content)
                nonCurrentDebt_Total =  item_content
            elif '負債總計' in item_title:
                # print(item_title)
                debtTotal =  item_content
            elif ('股本合計' in item_title) or ('股本' == item_title and item_content != ''):
                # print(item_title)
                equity_CommonStock =  item_content
                # print(equity_CommonStock)
            elif '資本公積' in item_title:
                # print(item_title)
                equity_CapitalReserve =  item_content
            elif '保留盈餘（或累積虧損）合計' in item_title:
                # print(item_title)
                equity_RetainedEarnings =  item_content
            elif '其他權益合計' in item_title:
                # print(item_title)
                equity_Others =  item_content
            elif '權益總計' == item_title:
                # print(item_title)
                equity_Total =  item_content
        except:
            print('this tr no content')

    print("股本 " + str(equity_CommonStock))
    print("資產 " + str(assetTotal))
    print("權益總計 " + str(equity_Total))
    equity_Per_Share = int(equity_Total)/int(equity_CommonStock)*10
    print("每股淨值 " + str(equity_Per_Share))

    stock = Stock.objects.get(stock_code=stock_code)

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

@shared_task
def crawl_securities_income_sheet(stock_code, date_string):
    startDate = datetime.strptime(date_string, '%Y%m%d')
    stock = Stock.objects.get(stock_code=stock_code)

    year = startDate.year - 1911
    if startDate.month == 3:
        season = '1'
    elif startDate.month == 6:
        season = '2'
    elif startDate.month == 9:
        season = '3'
    elif startDate.month == 12:
        season = '4'

    # url = 'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year=110&season=3&co_id=2883&firstin=1'

    url = f'https://mops.twse.com.tw/mops/web/ajax_t164sb04?encodeURIComponent=1&id=&key=&TYPEK=sii&step=2&year={str(year)}&season={season}&co_id={stock_code}&firstin=1'

    # url = f'https://mops.twse.com.tw/mops/web/t164sb04?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock_code}&year={str(year)}&season={season}'
    print(url)

    payload = {'api_key': '7e4c75f026434078700eb374b9456d12', 'url': url}
    resp = requests.get('http://api.scraperapi.com', params=payload)

    # resp = requests.get(url)

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table',{'class':'hasBorder'})
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
            item_title = item.find_all('td')[0].getText()
            item_content = item.find_all('td')[1].getText().replace(' ','').replace(',','')
            if '收益合計' == item_title:
                print(item_title)
                revenue = item_content
            elif '支出及費用合計' == item_title:
                print(item_title)
                totalExpense =  item_content
            elif '稅前淨利（淨損）' in item_title:
                print(item_title)
                profitBeforeTax =  item_content
            elif '本期淨利（淨損）' in item_title:
                print(item_title)
                profitAfterTax =  item_content
            elif '其他綜合損益' == item_title and item_content != '':
                print(item_title)
                otherIncome =  item_content
            elif '本期綜合損益總額' in item_title:
                print(item_title)
                totalIncome =  item_content
            elif '基本每股盈餘' in item_title and item_content != '':
                print(item_title)
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
 
