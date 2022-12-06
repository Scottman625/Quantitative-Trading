from datetime import datetime, date
from stockCore.models import Stock, IncomeStatement, StockRecord, KeyValueSheetCurrent


def adjust_income_state_season_4_data_to_period_instead_of_year():
    stocks = Stock.objects.all()

    for stock in stocks:
        print(f'{stock.name} {stock.stock_code}')
        if IncomeStatement.objects.filter(stock=stock).count() != 0:
            statements = IncomeStatement.objects.filter(stock=stock)
            for statement in statements:
                if statement.date.month == 12:
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

def change_company_state_if_no_stock_record():
    stocks = Stock.objects.all()
    today = date.today()

    for stock in stocks:
        start_date = f'{today.year}-{today.month}-01'
        if StockRecord.objects.filter(stock=stock, date__gte = start_date, date__lte = today).count() == 0 and stock.stockIndustry != '公司不繼續公開發行' and stock.stockIndustry != '此代號非公司' and stock.stockIndustry != '公司已下市':
            
            print(f'{stock.name} {stock.stock_code}')
            stock.stockIndustry = '公司已下市'
            stock.save()

            if KeyValueSheetCurrent.objects.filter(stock=stock).count() != 0:
                KeyValueSheetCurrent.objects.filter(stock=stock).delete()