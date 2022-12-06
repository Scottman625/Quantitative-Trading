from stockCore.models import Stock, CashFlowStatement, StockRecord, BalanceSheet, IntrinsicValueSheet, KeyValueSheetSeason
from celery import shared_task
from scipy.stats import gmean
import numpy as np

#from stockCrawler.tasks.task_cal_intrinsic_value import *

@shared_task
def cal_intrinsic_value(stock_code):
    stock = Stock.objects.get(stock_code=stock_code)

    balanceSheet = BalanceSheet.objects.filter(stock = stock).order_by('-date')[0]

    if IntrinsicValueSheet.objects.filter(stock_code=stock_code).count() != 0:
        intrinsicValueSheet = IntrinsicValueSheet.objects.get(stock_code=stock_code)
    else:
        intrinsicValueSheet = IntrinsicValueSheet()
        intrinsicValueSheet.stock = stock
        intrinsicValueSheet.stock_code = stock_code
    
    intrinsicValueSheet.cal_date = balanceSheet.date
    intrinsicValueSheet.balanceSheetCash = balanceSheet.CurrentAssets_Cash
    intrinsicValueSheet.balanceSheetDebtTotal = balanceSheet.DebtTotal
    intrinsicValueSheet.balanceSheetCommonStockShare = balanceSheet.Equity_CommonStock

    try:
        cashFlowStatement = CashFlowStatement.objects.get(date=balanceSheet.date, stock_code=stock_code)
    except:
        cashFlowStatement = CashFlowStatement.objects.filter(stock = stock).order_by('-date')[0]
    
    if cashFlowStatement.date.month == 12:
        intrinsicValueSheet.recentFourSeasonCashFlow = cashFlowStatement.NetCashFlow
    elif cashFlowStatement.date.month == 9:
        intrinsicValueSheet.recentFourSeasonCashFlow = cashFlowStatement.NetCashFlow  
        try:
            query_date_1 = f'{cashFlowStatement.date.year-1}-12-31'
            incomeStatement1 = CashFlowStatement.objects.get(date=query_date_1, stock_code=stock_code)

            query_date_2 = f'{cashFlowStatement.date.year-1}-09-30'
            incomeStatement2 = CashFlowStatement.objects.get(date=query_date_2, stock_code=stock_code)
            
            #Q4-Q3
            differenceCashFlow = incomeStatement1.NetCashFlow - incomeStatement2.NetCashFlow
            intrinsicValueSheet.recentFourSeasonCashFlow = intrinsicValueSheet.recentFourSeasonCashFlow + differenceCashFlow
        except:
            print("lack  1 cashflow data")
    elif cashFlowStatement.date.month == 6:
        intrinsicValueSheet.recentFourSeasonCashFlow = cashFlowStatement.NetCashFlow 
        try:
            query_date_1 = f'{cashFlowStatement.date.year-1}-12-31'
            incomeStatement1 = CashFlowStatement.objects.get(date=query_date_1, stock_code=stock_code)

            query_date_2 = f'{cashFlowStatement.date.year-1}-06-30'
            incomeStatement2 = CashFlowStatement.objects.get(date=query_date_2, stock_code=stock_code)
            
            #Q4-Q2
            differenceCashFlow = incomeStatement1.NetCashFlow - incomeStatement2.NetCashFlow
            intrinsicValueSheet.recentFourSeasonCashFlow = intrinsicValueSheet.recentFourSeasonCashFlow + differenceCashFlow
        except:
            print("lack 2 cashflow data")
    elif cashFlowStatement.date.month == 3:
        intrinsicValueSheet.recentFourSeasonCashFlow = cashFlowStatement.NetCashFlow  
        try:
            query_date_1 = f'{cashFlowStatement.date.year-1}-12-31'
            incomeStatement1 = CashFlowStatement.objects.get(date=query_date_1, stock_code=stock_code)

            query_date_2 = f'{cashFlowStatement.date.year-1}-03-31'
            incomeStatement2 = CashFlowStatement.objects.get(date=query_date_2, stock_code=stock_code)
            
            #Q4-Q1
            differenceCashFlow = incomeStatement1.NetCashFlow - incomeStatement2.NetCashFlow
            intrinsicValueSheet.recentFourSeasonCashFlow = intrinsicValueSheet.recentFourSeasonCashFlow + differenceCashFlow
        except:
            print("lack 3 cashflow data")

    print(intrinsicValueSheet.recentFourSeasonCashFlow)

    if intrinsicValueSheet.recentFourSeasonCashFlow > 0:
        #Recent 2 year positive ROE Growth rate compare to last year, and cal geometric mean
        try:
            roeRates = list(KeyValueSheetSeason.objects.filter(stock_code=stock_code).order_by('-date')[0:8].values_list('ROEGrowthRate1Year',flat=True))
            # print(roeRates)
            roeRates.sort()
            postiveRoeRates = [x for x in roeRates if x > 0]
            if len(postiveRoeRates) >= 6:
                print("more than 6 month positive roe growthrate")
                postiveRoeRates = postiveRoeRates[:len(postiveRoeRates)-1]
                postiveRoeRates.append(1)
                # print(postiveRoeRates)
                og_array =  np.array(postiveRoeRates)
                int_array = og_array.astype(int)
                # print(int_array)
                intrinsicValueSheet.growthRate = gmean(int_array)
                print("final roe growth rate")
                print(intrinsicValueSheet.growthRate)
            elif len(postiveRoeRates) == 5:
                print("5 month positive roe growthrate")
                postiveRoeRates = postiveRoeRates[:len(postiveRoeRates)-1]
                # print(postiveRoeRates)
                postiveRoeRates.append(1)
                postiveRoeRates.append(1)
                og_array =  np.array(postiveRoeRates)
                int_array = og_array.astype(int)
                # print(int_array)
                intrinsicValueSheet.growthRate = gmean(int_array)
                print("final roe growth rate")
                print(intrinsicValueSheet.growthRate)
            else:
                intrinsicValueSheet.growthRate = 0
        except:
            intrinsicValueSheet.growthRate = 0
            # keySeasonSheet = KeyValueSheetSeason.objects.filter(stock_code=stock_code).order_by('-date')[0]
            # print(keySeasonSheet.ROEGrowthRate1Year)
            # intrinsicValueSheet.growthRate = keySeasonSheet.ROEGrowthRate1Year

        intrinsicValueSheet.discountRate = 5.0
        
        try:
            intrinsicValueSheet.finalPERatio = float(stock.category.avgPEStr) * 0.7
            if intrinsicValueSheet.finalPERatio < 10:
                intrinsicValueSheet.finalPERatio = 10
        except:
            intrinsicValueSheet.finalPERatio = 12

        FCFArray = []
        FCFArray.append(float(intrinsicValueSheet.recentFourSeasonCashFlow))
        FCFDiscountedArray = []
        FCFDiscountedArray.append(float(intrinsicValueSheet.recentFourSeasonCashFlow))
        for x in range(1,11):
            theYearFCF = FCFArray[-1]*(1+float(intrinsicValueSheet.growthRate)/100)
            FCFArray.append(theYearFCF)
            # print(theYearFCF)

            theYearDiscountFCF = theYearFCF / pow((1+float(intrinsicValueSheet.discountRate)/100),x)
            FCFDiscountedArray.append(theYearDiscountFCF)
            print(theYearDiscountFCF)
        
        sumFCF = sum(FCFDiscountedArray)
        lastValue = FCFDiscountedArray[-1]*intrinsicValueSheet.finalPERatio

        intrinsicValueSheet.intrinsicPrice = 10 * (sumFCF + lastValue + float(intrinsicValueSheet.balanceSheetCash) - float(intrinsicValueSheet.balanceSheetDebtTotal)) / float(intrinsicValueSheet.balanceSheetCommonStockShare)
        intrinsicValueSheet.save()
    else:
        intrinsicValueSheet.growthRate = 0
        intrinsicValueSheet.discountRate = 5.0
        intrinsicValueSheet.finalPERatio = 10
        intrinsicValueSheet.intrinsicPrice = 0
        intrinsicValueSheet.save()

@shared_task
def compare_intrinsic_value(stock_code):
    if IntrinsicValueSheet.objects.filter(stock_code=stock_code).count() != 0:
        intrinsicValueSheet = IntrinsicValueSheet.objects.get(stock_code=stock_code)

        print(intrinsicValueSheet.stock.name)

        record = StockRecord.objects.filter(stock=intrinsicValueSheet.stock).last()

        intrinsicValueSheet.compare_date = record.date
        intrinsicValueSheet.compare_price = record.ClosingPrice
        intrinsicValueSheet.Dir = record.Dir
        intrinsicValueSheet.Change = record.Change
        intrinsicValueSheet.differenceInPrice = intrinsicValueSheet.intrinsicPrice - intrinsicValueSheet.compare_price 
        intrinsicValueSheet.differencePercent = (intrinsicValueSheet.intrinsicPrice - intrinsicValueSheet.compare_price) / intrinsicValueSheet.compare_price * 100
        intrinsicValueSheet.save()
