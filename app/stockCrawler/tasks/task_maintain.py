from celery import shared_task
from stockCore.models import Stock, BalanceSheet, IncomeStatement, CashFlowStatement, Category, KeyValueSheetSeason, KeyValueSheetCurrent, StockEvaluate, StockRecord, IntrinsicValueSheet
from datetime import datetime, date
from django.db.models import Avg

@shared_task
def crawl_stocks_month_revenues_by_date(date_string):
    # ex. crawl_company_revenue('20211001')
    from stockCrawler.tasks.tasks import crawl_company_revenue, crawl_tpex_company_revenue, crawl_foreign_company_revenue, crawl_foreign_tpex_company_revenue
    crawl_company_revenue(date_string)
    crawl_tpex_company_revenue(date_string)
    crawl_foreign_company_revenue(date_string)
    crawl_foreign_tpex_company_revenue(date_string)

@shared_task
def crawl_stocks_balance_sheet_by_date(date_string):
    from stockCrawler.tasks.tasks import crawl_company_balance_sheet
    from stockCrawler.tasks.task_crawl_financial_stocks import crawl_bank_balance_sheet, crawl_insurance_balance_sheet, crawl_securities_balance_sheet
    theDate = datetime.strptime(date_string, '%Y%m%d')
    stocks = Stock.objects.all()

    for stock in stocks:
        if BalanceSheet.objects.filter(stock=stock, date=theDate).count() == 0:
            if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and len(stock.stock_code)==4 and stock.category != Category.objects.get(id=26) and stock.category != Category.objects.get(id=29) and stock.category != Category.objects.get(id=32):
                crawl_company_balance_sheet.delay(stock.stock_code, date_string)
            elif stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and len(stock.stock_code)==4  and ( stock.category == Category.objects.get(id=26) or stock.category == Category.objects.get(id=32) ):
                banck_codes = '5880, 5876, 2897, 2892, 2891, 2890, 2889, 2888, 2887, 2886, 2885, 2884, 2883, 2882, 2881, 2880, 2849, 2845, 2838, 2836, 2834, 2812, 2809, 2801'
                insurance_codes = '2867, 2852, 2851, 2850, 2832, 2823, 2816'
                securities_codes = '5864, 6026, 5878, 6023, 6021, 6020, 6016, 6015, 5820, 6024, 6005, 2855, 2820'
                if(stock.stock_code in banck_codes):
                    crawl_bank_balance_sheet.delay(stock.stock_code, date_string)
                elif(stock.stock_code in insurance_codes):
                    crawl_insurance_balance_sheet.delay(stock.stock_code, date_string)
                elif(stock.stock_code in securities_codes):
                    crawl_securities_balance_sheet.delay(stock.stock_code, date_string)

# @shared_task
# def crawl_stocks_share_holder_by_date(date_string):
#     from stockCrawler.tasks.tasks import crawl_stock_share_holder
#     theDate = datetime.strptime(date_string, '%Y%m%d')
#     balanceSheets = BalanceSheet.objects.filter(date=theDate)

#     for sheet in balanceSheets:
#         if sheet.DirectorSupervisorShares == 0:
#             crawl_stock_share_holder.delay(sheet.stock_code, date_string)

@shared_task
def crawl_stocks_income_statement_by_date(date_string):
    from stockCrawler.tasks.tasks import crawl_company_income_sheet
    from stockCrawler.tasks.task_crawl_financial_stocks import crawl_bank_income_sheet, crawl_insurance_income_sheet, crawl_securities_income_sheet
    theDate = datetime.strptime(date_string, '%Y%m%d')
    balanceSheets = BalanceSheet.objects.filter(date=theDate)

    for sheet in balanceSheets:
        stock = sheet.stock
        if  stock.category != Category.objects.get(id=26) and stock.category != Category.objects.get(id=32) :
            crawl_company_income_sheet.delay(sheet.stock_code, date_string)
        elif stock.category == Category.objects.get(id=26) or stock.category == Category.objects.get(id=32) :
            banck_codes = '5880, 5876, 2897, 2892, 2891, 2890, 2889, 2888, 2887, 2886, 2885, 2884, 2883, 2882, 2881, 2880, 2849, 2845, 2838, 2836, 2834, 2812, 2809, 2801'
            insurance_codes = '2867, 2852, 2851, 2850, 2832, 2823, 2816'
            securities_codes = '5864, 6026, 5878, 6023, 6021, 6020, 6016, 6015, 5820, 6024, 6005, 2855, 2820'
            if(sheet.stock_code in banck_codes):
                crawl_bank_income_sheet.delay(sheet.stock_code, date_string)
            elif(sheet.stock_code in insurance_codes):
                crawl_insurance_income_sheet.delay(sheet.stock_code, date_string)
            elif(sheet.stock_code in securities_codes):
                crawl_securities_income_sheet.delay(sheet.stock_code, date_string)

@shared_task
def crawl_stocks_cashflow_statement_by_date(date_string):
    from stockCrawler.tasks.tasks import crawl_cash_flow_statement
    theDate = datetime.strptime(date_string, '%Y%m%d')
    balanceSheets = BalanceSheet.objects.filter(date=theDate)

    for sheet in balanceSheets:
        crawl_cash_flow_statement.delay(sheet.stock_code, date_string)

#這邊用手動會比較好~ 
#用 task_new_stock 配合爬公開資訊站的資料去處理比較好
# def crawl_stock_info():
#     from stockCrawler.tasks.tasks import crawl_stock_info
#     stocks = Stock.objects.filter(stockIndustry='')

#     for stock in stocks:
#         crawl_stock_info(stock.stock_code)

def crawl_stock_dividend():
    from stockCrawler.tasks.tasks import crawl_dividend_policy
    stocks = Stock.objects.all()

    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '公司已下市':
            crawl_dividend_policy.delay(stock.stock_code)

def calculate_history_season_key_values(date_string):
    from stockCrawler.tasks.tasks import calculate_season_key_values
    theDate = datetime.strptime(date_string, '%Y%m%d')
    
    stocks = Stock.objects.all()

    for stock in stocks:
        if BalanceSheet.objects.filter(stock=stock, date=theDate).count() != 0:
            calculate_season_key_values(stock.stock_code, date_string)

def calculate_all_stock_intrinsic_value(date_string):
    from stockCrawler.tasks.task_cal_intrinsic_value import cal_intrinsic_value
    theDate = datetime.strptime(date_string, '%Y%m%d')
    balanceSheets = BalanceSheet.objects.filter(date=theDate)

    for sheet in balanceSheets:
        cal_intrinsic_value.delay(sheet.stock_code)

#need to do every day
def compare_all_stock_intrinsic_value():
    from stockCrawler.tasks.task_cal_intrinsic_value import compare_intrinsic_value
    sheets = IntrinsicValueSheet.objects.all()

    for sheet in sheets:
        compare_intrinsic_value.delay(sheet.stock_code)

#need to do every day
def calculate_all_stocks_current_key_value():
    from stockCrawler.tasks.tasks import calculate_current_key_values
    stocks = Stock.objects.all()
    
    for stock in stocks:
        if stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市' and KeyValueSheetSeason.objects.filter(stock=stock).count() != 0:
            calculate_current_key_values(stock.stock_code)

#do at every saturday
def calcuate_all_stocks_evalutate(date_string):
    from stockCrawler.tasks.tasks import calculate_stock_evalutate
    stocks = Stock.objects.all()

    for stock in stocks:
        if KeyValueSheetCurrent.objects.filter(stock=stock).count() != 0:
            calculate_stock_evalutate(stock.stock_code, date_string)
        elif StockEvaluate.objects.filter(stock=stock).count() != 0:
            StockEvaluate.objects.filter(stock=stock).delete()

def calculate_category_avgs():
    import statistics
    categories = Category.objects.all()

    for category in categories:
        stockSheets = KeyValueSheetCurrent.objects.filter(category=category).filter(PriceEarningRatio__gte=0).filter(PriceEarningRatio__lte=1000).filter(Yield__lte=100).filter(EPS__lte=1000).filter(GrossMargin__lte=100).filter(GrossMargin__gte=0)
        avgPE = stockSheets.aggregate(Avg('PriceEarningRatio'))
        avgMarketValue = stockSheets.aggregate(Avg('MarketValue'))
        avgYield = stockSheets.aggregate(Avg('Yield'))
        avgROE = stockSheets.aggregate(Avg('ReturnOfEquity'))
        avgEPS = stockSheets.aggregate(Avg('EPS'))
        avgGrossMargin = stockSheets.aggregate(Avg('GrossMargin'))
        avgDebtAssetRatio = stockSheets.aggregate(Avg('DebtAssetRatio'))
        avgEPSGrowthRate5Years = stockSheets.aggregate(Avg('EPSGrowthRate5Years'))

        avgPEStr = str(avgPE['PriceEarningRatio__avg'])
        try:
            index = avgPEStr.index('.')
            category.avgPEStr = avgPEStr[0:index+3]
        except:
            category.avgPEStr = avgPEStr

        avgMarketValueStr = str(avgMarketValue['MarketValue__avg'])
        try:
            index = avgMarketValueStr.index('.')
            category.avgMarketValueStr = avgMarketValueStr[0:index]
        except:
            category.avgMarketValueStr = avgMarketValueStr

        avgYieldStr = str(avgYield['Yield__avg'])
        try:
            index = avgYieldStr.index('.')
            category.avgYieldStr = avgYieldStr[0:index+3]+'%'
        except:
            category.avgYieldStr = avgYieldStr+'%'
        
        avgROEStr = str(avgROE['ReturnOfEquity__avg'])
        try:
            index = avgROEStr.index('.')
            category.avgROEStr = avgROEStr[0:index+3]+'%'
        except:
            category.avgROEStr = avgROEStr+'%'

        
        avgEPSStr = str(avgEPS['EPS__avg'])
        try:
            index = avgEPSStr.index('.')
            category.avgEPSStr = avgEPSStr[0:index+3]
        except:
            category.avgEPSStr = avgEPSStr

        
        avgGrossMarginStr = str(avgGrossMargin['GrossMargin__avg'])
        try:
            index = avgGrossMarginStr.index('.')
            category.avgGrossMarginStr = avgGrossMarginStr[0:index+3]+'%'
        except:
            category.avgGrossMarginStr = avgGrossMarginStr+'%'
        
        avgDebtAssetRatioStr = str(avgDebtAssetRatio['DebtAssetRatio__avg'])
        try:
            index = avgDebtAssetRatioStr.index('.')
            category.avgDebtAssetRatioStr = avgDebtAssetRatioStr[0:index+3]+'%'
        except:
            category.avgDebtAssetRatioStr = avgDebtAssetRatioStr+'%'
        
        avgEPSGrowthRate5YearsStr = str(avgEPSGrowthRate5Years['EPSGrowthRate5Years__avg'])
        try:
            index = avgEPSGrowthRate5YearsStr.index('.')
            category.avgEPSGrowthRate5YearsStr = avgEPSGrowthRate5YearsStr[0:index+3]+'%'
        except:
            category.avgEPSGrowthRate5YearsStr = avgEPSGrowthRate5YearsStr+'%'
        
        category.save()

def make_all_stock_ranks():
    stockSheets = KeyValueSheetCurrent.objects.all()
    for stockSheet in stockSheets:
        make_stock_ranks(stockSheet.stock_code)

def make_stock_ranks(stock_code):
    theStockKeySheet = KeyValueSheetCurrent.objects.get(stock_code=stock_code)
    stockSheets = KeyValueSheetCurrent.objects.filter(category=theStockKeySheet.category)
    
    print(theStockKeySheet.stock_name+theStockKeySheet.stock_code)

    num = stockSheets.count()
    theStockKeySheet.CategoryNum = num

    allKeySheets = stockSheets.order_by('PriceEarningRatio')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankPriceEarningRatio = index
    # print('PriceEarningRatio: ' + str(index) + '/'+ str(num))

    allKeySheets = stockSheets.order_by('-MarketValue')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankMarketValue = index
    # print('MarketValue: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('-Yield')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankYield = index
    # print('Yield: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('-EPS')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankEPS = index
    # print('EPS: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('-ReturnOfEquity')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankReturnOfEquity = index
    # print('ReturnOfEquity: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('-PriceBookRatio')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankPriceBookRatio = index
    # print('PriceBookRatio: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('-GrossMargin')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankGrossMargin = index
    # print('GrossMargin: ' + str(index)+ '/'+ str(num))

    allKeySheets = stockSheets.order_by('DebtAssetRatio')
    index = list(allKeySheets).index(theStockKeySheet)+1
    theStockKeySheet.RankDebtAssetRatio = index
    # print('DebtAssetRatio: ' + str(index)+ '/'+ str(num))

    theStockKeySheet.save()

def update_all_key_value_sheet_current_record():
    sheets = KeyValueSheetCurrent.objects.all()
    for sheet in sheets:
        update_key_value_sheet_current_record(sheet.stock_code)

def update_key_value_sheet_current_record(stock_code):
    sheet = KeyValueSheetCurrent.objects.get(stock_code=stock_code)
    record = StockRecord.objects.filter(stock=sheet.stock).last()

    sheet.date = record.date
    sheet.ClosingPrice = record.ClosingPrice
    sheet.CurrentStockPrice = record.ClosingPrice
    sheet.Dir = record.Dir
    sheet.Change = record.Change
    sheet.Volume = record.Volume
    sheet.save()

    print(sheet.date.strftime("%Y%m%d")+ ' ' + sheet.stock_name + ' ' + str(sheet.ClosingPrice))

def calculate_price_limit_up_down():
    sheets = KeyValueSheetCurrent.objects.all()
    
    for keyValueSheetCurrent in sheets:
        print(keyValueSheetCurrent.stock)

        keyValueSheetCurrent.isLimitUp = False
        keyValueSheetCurrent.isLimitDown = False

        todayStockRecord = StockRecord.objects.filter(stock=keyValueSheetCurrent.stock).order_by('-date')[0]

        if(todayStockRecord.Dir == '+'):
            upPercent = todayStockRecord.Change / (todayStockRecord.ClosingPrice - todayStockRecord.Change)
            if(upPercent>= 0.09):
                keyValueSheetCurrent.isLimitUp = True
        elif(todayStockRecord.Dir == '-'):
            downPercent = todayStockRecord.Change / (todayStockRecord.ClosingPrice + todayStockRecord.Change)
            if(downPercent>= 0.09):
                keyValueSheetCurrent.isLimitDown = True
        
        keyValueSheetCurrent.save()

def update_stocks_season_key_values(stock_code):
    from stockCrawler.tasks.tasks import calculate_season_key_values
    stock = Stock.objects.get(stock_code=stock_code)

    sheets = BalanceSheet.objects.filter(stock=stock).order_by('date')
    for sheet in sheets:
        date_string = sheet.date.strftime("%Y%m%d")
        calculate_season_key_values(stock.stock_code, date_string)

    from stockCrawler.tasks.tasks import calculate_current_key_values
    calculate_current_key_values(stock_code)