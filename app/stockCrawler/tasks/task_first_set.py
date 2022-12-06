from datetime import datetime, date as thedate, timedelta
from stockCore.models import Stock, RevenueSheet, Category, DividendSheet, CashFlowStatement, IncomeStatement, BalanceSheet, StockRecord, KeyValueSheetSeason, KeyValueSheetCurrent, StockEvaluate, Index
import time
import random

def crawl_history_twse_stock():
    from stockCrawler.tasks.task_twse import crawl_the_day_stock_price_and_index
    
    start_date = thedate(2004, 2, 11)
    end_date = thedate.today()
    delta = timedelta(days=1)

    while start_date < end_date:
        crawl_the_day_stock_price_and_index.delay(start_date.strftime("%Y%m%d"))

        start_date = start_date + delta

def crawl_history_tpex_stock():
    from stockCrawler.tasks.tasks_tpex import crawl_the_day_tpex_stock_price

    start_date = thedate(2007, 4, 20)
    end_date = thedate.today()
    delta = timedelta(days=1)

    while start_date < end_date:
        date_string = start_date.strftime('%Y%m%d')    
        crawl_the_day_tpex_stock_price.delay(date_string)

        start_date = start_date + delta

def crawl_all_stock_info():
    from stockCrawler.tasks.tasks import crawl_stock_info
    stocks = Stock.objects.all()

    for stock in stocks:
        crawl_stock_info.delay(stock.stock_code)

def crawl_history_stock_month_revenue():
    from stockCrawler.tasks.tasks import crawl_company_revenue

    # data html in older date is a little different, so if want to get older data, need improve crawler
    startDate = thedate(2013,2,1)
    endDate = thedate(2021,9,1)

    while startDate < endDate:
        date_string = startDate.strftime("%Y%m%d")
        crawl_company_revenue.delay(date_string)

        try:
            startDate = startDate.replace(month=startDate.month+1)
        except ValueError:
            if startDate.month == 12:
                startDate = startDate.replace(year=startDate.year+1, month=1)
            else:
                # next month is too short to have "same date"
                # pick your own heuristic, or re-raise the exception:
                raise

def crawl_tpex_history_stock_month_revenue():
    from stockCrawler.tasks.tasks import crawl_tpex_company_revenue

    # data html in older date is a little different, so if want to get older data, need improve crawler
    startDate = thedate(2013,2,1)
    endDate = thedate(2021,9,1)

    while startDate < endDate:
        date_string = startDate.strftime("%Y%m%d")
        crawl_tpex_company_revenue(date_string)

        try:
            startDate = startDate.replace(month=startDate.month+1)
        except ValueError:
            if startDate.month == 12:
                startDate = startDate.replace(year=startDate.year+1, month=1)
            else:
                # next month is too short to have "same date"
                # pick your own heuristic, or re-raise the exception:
                raise

def crawl_ky_history_stock_month_revenue():
    from stockCrawler.tasks.tasks import crawl_foreign_company_revenue, crawl_foreign_tpex_company_revenue

    # data html in older date is a little different, so if want to get older data, need improve crawler
    startDate = thedate(2013,2,1)
    endDate = thedate(2021,11,1)

    while startDate < endDate:
        date_string = startDate.strftime("%Y%m%d")
        crawl_foreign_company_revenue(date_string)
        crawl_foreign_tpex_company_revenue(date_string)

        try:
            startDate = startDate.replace(month=startDate.month+1)
        except ValueError:
            if startDate.month == 12:
                startDate = startDate.replace(year=startDate.year+1, month=1)
            else:
                # next month is too short to have "same date"
                # pick your own heuristic, or re-raise the exception:
                raise

def crawl_history_stock_balance_sheet():
    from stockCrawler.tasks.tasks import crawl_company_balance_sheet
    stocks = Stock.objects.all()

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

            while startDate < end_date:
                date_string = startDate.strftime("%Y%m%d")
                crawl_company_balance_sheet.delay(stock.stock_code, date_string)

                if startDate.month == 3:
                    startDate = datetime(startDate.year,6,30)
                elif startDate.month == 6:
                    startDate = datetime(startDate.year,9,30)
                elif startDate.month == 9:
                    startDate = datetime(startDate.year,12,31)
                elif startDate.month == 12:
                    startDate = datetime(startDate.year+1,3,31)

def crawl_history_stock_share_hoder():
    from stockCrawler.tasks.tasks import crawl_stock_share_holder
    balanceSheets = BalanceSheet.objects.all()

    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        crawl_stock_share_holder.delay(sheet.stock_code, date_string)

def crawl_history_income_sheet():
    from stockCrawler.tasks.tasks import crawl_company_income_sheet
    balanceSheets = BalanceSheet.objects.all()

    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        crawl_company_income_sheet.delay(sheet.stock_code, date_string)

def crawl_history_cashflow_statement():
    from stockCrawler.tasks.tasks import crawl_cash_flow_statement
    balanceSheets = BalanceSheet.objects.all()

    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        crawl_cash_flow_statement.delay(sheet.stock_code, date_string)

def crawl_stock_dividend():
    from stockCrawler.tasks.tasks import crawl_dividend_policy
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '公司已下市':
            crawl_dividend_policy.delay(stock.stock_code)

def calculate_history_season_key_values():
    from stockCrawler.tasks.tasks import calculate_season_key_values
    stocks = Stock.objects.all()

    for stock in stocks:
        sheets = BalanceSheet.objects.filter(stock=stock).order_by('date')
        for sheet in sheets:
            date_string = sheet.date.strftime("%Y%m%d")
            calculate_season_key_values(stock.stock_code, date_string)

#need to do every day
def calculate_all_stocks_current_key_value():
    from stockCrawler.tasks.tasks import calculate_current_key_values
    stocks = Stock.objects.all()
    
    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and KeyValueSheetSeason.objects.filter(stock=stock).count() != 0:
            calculate_current_key_values(stock.stock_code)

#need to do every day
def calcuate_all_stocks_evalutate():
    from stockCrawler.tasks.tasks import calculate_stock_evalutate
    stocks = Stock.objects.all()

    for stock in stocks:
        if KeyValueSheetCurrent.objects.filter(stock=stock).count() != 0:
            calculate_stock_evalutate(stock.stock_code)
        elif StockEvaluate.objects.filter(stock=stock).count() != 0:
            StockEvaluate.objects.filter(stock=stock).delete()



################################
def check_all_stocks_info():
    from stockCrawler.tasks.tasks import crawl_stock_info
    stocks = Stock.objects.filter(stockIndustry='')

    for stock in stocks:
        crawl_stock_info.delay(stock.stock_code)

def check_month_revenues():
    from stockCrawler.tasks.tasks import crawl_company_revenue
    
    startDate = thedate(2013,2,1)
    endDate = thedate(2021,8,1)

    while startDate < endDate:
        date_string = startDate.strftime("%Y%m%d")

        if RevenueSheet.objects.filter(date=startDate, stock_code='2330').count() ==0:
            crawl_company_revenue.delay(date_string)

        try:
            startDate = startDate.replace(month=startDate.month+1)
        except ValueError:
            if startDate.month == 12:
                startDate = startDate.replace(year=startDate.year+1, month=1)
            else:
                # next month is too short to have "same date"
                # pick your own heuristic, or re-raise the exception:
                raise

def check_balance_sheet():
    from stockCrawler.tasks.tasks import crawl_company_balance_sheet, crawl_company_balance_sheet_ajax
    stocks = Stock.objects.all()

    for stock in stocks:

        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and len(stock.stock_code)==4 :
            #set start_date
            if BalanceSheet.objects.filter(stock=stock).count() != 0:
                startDate = BalanceSheet.objects.filter(stock=stock).order_by('date')[0].date
                end_date = datetime(2021,9,30).date()

                while startDate < end_date:
                    date_string = startDate.strftime("%Y%m%d")
                    if BalanceSheet.objects.filter(stock=stock, date=startDate).count()==0:
                        crawl_company_balance_sheet.delay(stock.stock_code, date_string)
                    else:                    
                        if BalanceSheet.objects.filter(stock=stock, date=startDate)[0].Equity_Total == 0:
                            crawl_company_balance_sheet.delay(stock.stock_code, date_string)
                        

                    if startDate.month == 3:
                        startDate = datetime(startDate.year,6,30).date()
                    elif startDate.month == 6:
                        startDate = datetime(startDate.year,9,30).date()
                    elif startDate.month == 9:
                        startDate = datetime(startDate.year,12,31).date()
                    elif startDate.month == 12:
                        startDate = datetime(startDate.year+1,3,31).date()
            # elif '金' not in stock.name and '銀' not in stock.name and '櫃' not in stock.name and '證' not in stock.name and '壽' not in stock.name and '保' not in stock.name and stock.category != Category.objects.get(id=26):
                # 金控類的先不處理
                # print(f'this stock no balancesheet data => id={stock.id} name={stock.name} stock_code={stock.stock_code}')
                # startDate = datetime(2013,3,31)

                # if StockRecord.objects.filter(stock=stock).order_by('date')[0].date > startDate.date():
                #     newDate = StockRecord.objects.filter(stock=stock).order_by('date')[0].date
                #     if newDate.month <= 3:
                #         startDate = datetime(newDate.year,3,31)
                #     elif newDate.month >= 4 and newDate.month <= 6:
                #         startDate = datetime(newDate.year,6,30)
                #     elif newDate.month >= 7 and newDate.month <= 9:
                #         startDate = datetime(newDate.year,9,30)
                #     elif newDate.month >= 10 and newDate.month <= 12:
                #         startDate = datetime(newDate.year,12,31)

                # end_date = datetime(2021,9,30)
                # while startDate < end_date:
                #     date_string = startDate.strftime("%Y%m%d")
                #     # crawl_company_balance_sheet_ajax.delay(stock.stock_code, date_string)
                #     crawl_company_balance_sheet.delay(stock.stock_code, date_string)

                #     if startDate.month == 3:
                #         startDate = datetime(startDate.year,6,30)
                #     elif startDate.month == 6:
                #         startDate = datetime(startDate.year,9,30)
                #     elif startDate.month == 9:
                #         startDate = datetime(startDate.year,12,31)
                #     elif startDate.month == 12:
                #         startDate = datetime(startDate.year+1,3,31)

def print_balance_sheet_common_stock_zero_stcoks():
    from stockCrawler.tasks.tasks import crawl_company_balance_sheet
    sheets = BalanceSheet.objects.filter(Equity_Total=0)

    for sheet in sheets:
        startDate = sheet.date
        date_string = startDate.strftime("%Y%m%d")
        stock = sheet.stock
        
        year = startDate.year - 1911
        if startDate.month == 3:
            season = '01'
        elif startDate.month == 6:
            season = '02'
        elif startDate.month == 9:
            season = '03'
        elif startDate.month == 12:
            season = '04'

        print(f'sheet_id={sheet.id} date_string={date_string} stock_id={stock.id} stock_name={stock.name} stock_code={stock.stock_code}')
        url = f'https://mops.twse.com.tw/mops/web/t164sb03?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4=&code1=&TYPEK2=&checkbtn=&queryName=co_id&inpuType=co_id&TYPEK=all&isnew=false&co_id={stock.stock_code}&year={str(year)}&season={season}'
        print(url)
        print('')
        print('')

        crawl_company_balance_sheet(stock.stock_code, date_string)
        time.sleep(random.randint(8,15))

def check_share_hoder():
    from stockCrawler.tasks.tasks import crawl_stock_share_holder
    balanceSheets = BalanceSheet.objects.filter(DirectorSupervisorShares=0)

    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        crawl_stock_share_holder.delay(sheet.stock_code, date_string)

def check_share_holder_and_assign_to_closest_data():
    balanceSheets = BalanceSheet.objects.filter(DirectorSupervisorShares=0)
    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        stock = sheet.stock
        print(f'sheet_id={sheet.id} date_string={date_string} stock_id={stock.id} stock_name={stock.name} stock_code={stock.stock_code}')
        stockBalanceSheets = BalanceSheet.objects.filter(stock=sheet.stock)
        closest_sheet = get_closest_to(stockBalanceSheets, sheet.date)
        sheet.DirectorSupervisorShares = closest_sheet.DirectorSupervisorShares
        sheet.DirectorSupervisorPledgeShares = closest_sheet.DirectorSupervisorPledgeShares
        sheet.save()

def check_income_sheet():
    from stockCrawler.tasks.tasks import crawl_company_income_sheet
    balanceSheets = BalanceSheet.objects.all()

    for sheet in balanceSheets:
        date_string = sheet.date.strftime("%Y%m%d")
        if IncomeStatement.objects.filter(stock=sheet.stock, date=sheet.date).count() == 0 or IncomeStatement.objects.get(stock=sheet.stock, date=sheet.date).EPS_Period == 0:
            crawl_company_income_sheet.delay(sheet.stock_code, date_string)
            
def check_income_sheet_and_crawl_by_device_own_proxy():
    from stockCrawler.tasks.tasks import crawl_company_income_sheet
    incomeSheets = IncomeStatement.objects.filter(EPS_Period=0)

    for index,sheet in enumerate(incomeSheets):
        if index > 200:
            print(index)
            date_string = sheet.date.strftime("%Y%m%d")
            crawl_company_income_sheet(sheet.stock_code, date_string)
            time.sleep(random.randint(8,15))

def check_cashflow_statement():
    from stockCrawler.tasks.tasks import crawl_cash_flow_statement
    balanceSheets = BalanceSheet.objects.all()

    for  sheet in balanceSheets:
        if CashFlowStatement.objects.filter(stock=sheet.stock, date=sheet.date).count()==0 or CashFlowStatement.objects.get(stock=sheet.stock, date=sheet.date).TotalAssetsCash == 0:
                date_string = sheet.date.strftime("%Y%m%d")
                crawl_cash_flow_statement.delay(sheet.stock_code, date_string)

def check_cashflow_sheet_and_crawl_by_device_own_proxy():
    from stockCrawler.tasks.tasks import crawl_cash_flow_statement
    cashFlowSheets = CashFlowStatement.objects.filter(TotalAssetsCash=0)

    for index,sheet in enumerate(cashFlowSheets):
        if index > 11:
            print(index)
            date_string = sheet.date.strftime("%Y%m%d")
            crawl_cash_flow_statement(sheet.stock_code, date_string)
            time.sleep(random.randint(8,15))

def check_stock_dividend():
    from stockCrawler.tasks.tasks import crawl_dividend_policy
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '公司已下市' and DividendSheet.objects.filter(stock=stock).count()==0:
            crawl_dividend_policy.delay(stock.stock_code)

def check_stock_dividend_and_crawl_by_device_own_proxy():
    from stockCrawler.tasks.tasks import crawl_dividend_policy
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '公司已下市' and DividendSheet.objects.filter(stock=stock).count()==0:
            try:
                crawl_dividend_policy(stock.stock_code)
            except:
                print('test the link, may no data!')

            time.sleep(random.randint(8,15))

def check_category():
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':
            try:
                category = Category.objects.get(name=stock.stockIndustry)
                stock.category = category
                stock.save()
            except:
                print(f'this stock cannot find category => id={stock.id} name={stock.name} stock_code={stock.stock_code}')

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

def check_calculate_history_season_key_values(stock_code):
    from stockCrawler.tasks.tasks import calculate_season_key_values
    stock = Stock.objects.get(stock_code=stock_code)

    sheets = BalanceSheet.objects.filter(stock=stock).order_by('date')
    for sheet in sheets:
        date_string = sheet.date.strftime("%Y%m%d")
        calculate_season_key_values(stock.stock_code, date_string)

################################################
def assign_stock_record_to_key_current_sheet():
    stocks = Stock.objects.all()

    for stock in stocks:
        if KeyValueSheetCurrent.objects.filter(stock=stock).count() != 0:
            sheet = KeyValueSheetCurrent.objects.filter(stock=stock)[0]
            record = StockRecord.objects.filter(stock=stock).order_by('-date')[0]
            sheet.ClosingPrice = record.ClosingPrice
            sheet.Dir = record.Dir
            sheet.Change = record.Change
            sheet.Volume = record.Volume
            sheet.save()
