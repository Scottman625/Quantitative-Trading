from datetime import datetime, date as thedate, timedelta
from stockCore.models import Stock, RevenueSheet, Category, DividendSheet, CashFlowStatement, IncomeStatement, BalanceSheet, StockRecord, KeyValueSheetSeason, KeyValueSheetCurrent, StockEvaluate, Index
import time
import random

def test_crawl_history_income_sheet(stock_code, start_date_string):
    from stockCrawler.tasks.tasks import crawl_company_income_sheet
    print(stock_code)
    stock = Stock.objects.get(stock_code=stock_code)
    startDate = datetime.strptime(start_date_string, '%Y%m%d')
    end_date = datetime(2022,6,30)

    while startDate <= end_date:
        date_string = startDate.strftime("%Y%m%d")
        crawl_company_income_sheet.delay(stock.stock_code, date_string)
        print(startDate)

        if startDate.month == 3:
            startDate = datetime(startDate.year,6,30)
        elif startDate.month == 6:
            startDate = datetime(startDate.year,9,30)
        elif startDate.month == 9:
            startDate = datetime(startDate.year,12,31)
        elif startDate.month == 12:
            startDate = datetime(startDate.year+1,3,31)

def test_crawl_cash_flow_statement(stock_code, start_date_string):
    from stockCrawler.tasks.tasks import crawl_cash_flow_statement
    print(stock_code)
    stock = Stock.objects.get(stock_code=stock_code)
    startDate = datetime.strptime(start_date_string, '%Y%m%d')
    end_date = datetime(2022,6,30)

    while startDate <= end_date:
        date_string = startDate.strftime("%Y%m%d")
        crawl_cash_flow_statement.delay(stock.stock_code, date_string)
        print(startDate)

        if startDate.month == 3:
            startDate = datetime(startDate.year,6,30)
        elif startDate.month == 6:
            startDate = datetime(startDate.year,9,30)
        elif startDate.month == 9:
            startDate = datetime(startDate.year,12,31)
        elif startDate.month == 12:
            startDate = datetime(startDate.year+1,3,31)
