from datetime import datetime, date
from stockCrawler.tasks.tasks import crawl_company_balance_sheet, crawl_stock_share_holder, crawl_company_income_sheet, crawl_cash_flow_statement, crawl_stock_info, crawl_dividend_policy, calculate_season_key_values, calculate_current_key_values, calculate_stock_evalutate
from stockCore.models import Stock, DividendSheet

def crawl_new_stock_datas(stock_code, start_date_string, end_date_string):
    stock = Stock.objects.get(stock_code=stock_code)
    if stock.stockChairman == '' :
        crawl_stock_info(stock_code)
    if DividendSheet.objects.filter(stock_code=stock_code).count==0 :
        crawl_dividend_policy(stock_code)

    start_date  = datetime.strptime(start_date_string, '%Y%m%d')
    end_date = datetime.strptime(end_date_string, '%Y%m%d')

    while start_date <= end_date:
        date_string = start_date.strftime("%Y%m%d")
        crawl_company_balance_sheet(stock_code,date_string)
        # crawl_stock_share_holder(stock_code,date_string)
        crawl_company_income_sheet(stock_code,date_string)
        crawl_cash_flow_statement(stock_code,date_string)
        calculate_season_key_values(stock_code,date_string)

        if start_date.month == 3:
            start_date = datetime(start_date.year,6,30)
        elif start_date.month == 6:
            start_date = datetime(start_date.year,9,30)
        elif start_date.month == 9:
            start_date = datetime(start_date.year,12,31)
        elif start_date.month == 12:
            start_date = datetime(start_date.year+1,3,31)

    
    calculate_current_key_values(stock_code)

    todayString = date.today().strftime("%Y%m%d")
    calculate_stock_evalutate(stock_code, todayString)