# from stockCore.models import KeyValueIndex, FilterCondition, UserFilterCondition, User, InterestRate, Stock
from stockCore.models import User,Stock
from datetime import datetime
import csv
import os


def import_stocks():
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'stocks.csv')

    file = open(file_path)
    reader = csv.reader(file, delimiter=',')
    for index, row in enumerate(reader):
        if index != 0:
            if Stock.objects.filter(stock_code=row[0]).count()==0:
                stock = Stock()
            else:
                stock = Stock.objects.filter(stock_code=row[0]).first()
            
            stock.stock_code = row[0]
            stock.name = row[1]
            stock.stockIndustry = row[2]
            stock.stockFullName = row[3]
            stock.stockAddress = row[4]
            stock.stockChairman = row[5]
            stock.stockManager = row[6]
            stock.stockMainBusiness = row[7]
            stock.stockCreatedDate = row[8]
            stock.stockCapital = row[9]
            stock.stockIPODate = row[10]
            stock.stockState = row[11]
            stock.stockCommonSharePrice = row[12]
            stock.stockCommonShares = row[13]
            stock.stockDividendFrequency = row[14]
            stock.stockCompanyURL = row[15]
            stock.stockMoneyDJIntroduceURL = row[16]
            stock.save()

            print(stock.name + " " + stock.stock_code)

# def create_key_value_index():
#     KeyValueIndex.objects.create(name='本益比', type='key_index', variable_column='PriceEarningRatio')
#     KeyValueIndex.objects.create(name='市值', type='key_index', variable_column='MarketValue')
#     KeyValueIndex.objects.create(name='股利', type='key_index', variable_column='Dividend')
#     KeyValueIndex.objects.create(name='EPS', type='key_index', variable_column='EPS')
#     KeyValueIndex.objects.create(name='殖利率', type='key_index', variable_column='Yield')
#     KeyValueIndex.objects.create(name='ROE', type='key_index', variable_column='ReturnOfEquity')
#     KeyValueIndex.objects.create(name='ROA', type='key_index', variable_column='ReturnOfAssets')
#     KeyValueIndex.objects.create(name='股票淨值比', type='key_index', variable_column='PriceBookRatio')
#     KeyValueIndex.objects.create(name='毛利率', type='key_index', variable_column='GrossMargin')
#     KeyValueIndex.objects.create(name='稅後淨利率', type='key_index', variable_column='NetProfitAfterTaxMargin')
#     KeyValueIndex.objects.create(name='負債資產比', type='key_index', variable_column='DebtAssetRatio')

#     KeyValueIndex.objects.create(name='近五年EPS成長率', type='growth_index', variable_column='EPSGrowthRate5Years')
#     KeyValueIndex.objects.create(name='近五年ROE成長率', type='growth_index', variable_column='ROEGrowthRate5Years')
#     KeyValueIndex.objects.create(name='近五年營收成長率', type='growth_index', variable_column='RevenueGrowthRate5Years')
#     KeyValueIndex.objects.create(name='近一年EPS成長率', type='growth_index', variable_column='EPSGrowthRate1Year')
#     KeyValueIndex.objects.create(name='近一年ROE成長率', type='growth_index', variable_column='ROEGrowthRate1Year')
#     KeyValueIndex.objects.create(name='近一年營收成長率', type='growth_index', variable_column='RevenueGrowthRate1Year')

# def create_filter_conditions():
#     FilterCondition.objects.create(title='大師選股', selections='無,巴菲特,彼得林區', variable_column='Master', usage='often')
#     FilterCondition.objects.create(title='市值', selections='無,>1000億,>500億,>100億,>50億,>20億,>10億', variable_column='MarketValue', usage='often')
#     FilterCondition.objects.create(title='產業', selections='無,水泥工業,食品工業,塑膠工業,紡織纖維,電機機械,電器電纜,化學工業,生技醫療業,玻璃陶瓷,造紙工業,鋼鐵工業,橡膠工業,汽車工業,半導體業,光電業,通信網路業,電子零組件業,電子通路業,資訊服務業,其他電子業,油電燃氣業,建材營造,航運業,觀光事業,金融保險業,貿易百貨', variable_column='Category', usage='often')
#     FilterCondition.objects.create(title='本益比', selections='無,<5,<10,<15,<20,<30', variable_column='PriceEarningRatio', usage='often')
#     FilterCondition.objects.create(title='殖利率', selections='無,>8%,>5%,>3%,>2%,>1%', variable_column='Yield', usage='often')
#     FilterCondition.objects.create(title='EPS', selections='無,>20,>15,>10,>5,>0', variable_column='EPS', usage='often')
#     FilterCondition.objects.create(title='ROE', selections='無,>25%,>20%,>15%,>10%,>5%,>0%', variable_column='ReturnOfEquity', usage='often')
#     FilterCondition.objects.create(title='ROA', selections='無,>25%,>20%,>15%,>10%,>5%,>0%', variable_column='ReturnOfAssets', usage='often')
#     FilterCondition.objects.create(title='P/B股價淨值比', selections='無,<1,<2,<3,<5,<10,<20', variable_column='PriceBookRatio', usage='often')
#     FilterCondition.objects.create(title='毛利率', selections='無,>60%,>50%,>40%,>30%,>20%,>10%,>0%', variable_column='GrossMargin', usage='often')
#     FilterCondition.objects.create(title='營業利益率', selections='無,>50%,>40%,>30%,>20%,>10%,>0%', variable_column='OperatingMargin', usage='often')
#     FilterCondition.objects.create(title='稅後淨利率', selections='無,>50%,>40%,>30%,>20%,>10%,>0%', variable_column='NetProfitAfterTaxMargin', usage='often')
#     FilterCondition.objects.create(title='負債資產比', selections='無,<5%,<10%,<15%,<20%,<25%,<30%,<40%,<50%', variable_column='DebtAssetRatio', usage='often')
#     FilterCondition.objects.create(title='EPS近五年平均成長率', selections='無,>20%,>15%,>10%,>5%,>0%', variable_column='EPSGrowthRate5Years', usage='often')
#     FilterCondition.objects.create(title='ROE近五年平均成長率', selections='無,>20%,>15%,>10%,>5%,>0%', variable_column='ROEGrowthRate5Years', usage='often')
#     FilterCondition.objects.create(title='營收近五年平均成長率', selections='無,>20%,>15%,>10%,>5%,>0%', variable_column='RevenueGrowthRate5Years', usage='often')

#     FilterCondition.objects.create(title='EPS近一年成長率', selections='無,>30%,>20%,>15%,>10%,>5%,>0%', variable_column='EPSGrowthRate1Year', usage='not_often')
#     FilterCondition.objects.create(title='ROE近一年成長率', selections='無,>30%,>20%,>15%,>10%,>5%,>0%', variable_column='ROEGrowthRate1Year', usage='not_often')
#     FilterCondition.objects.create(title='營收近一年成長率', selections='無,>30%,>20%,>15%,>10%,>5%,>0%', variable_column='RevenueGrowthRate1Year', usage='not_often')
#     FilterCondition.objects.create(title='稅前盈利率', selections='無,>60%,>50%,>40%,>30%,>20%,>10%,>0%', variable_column='NetProfitBeforeTaxMargin', usage='not_often')
#     FilterCondition.objects.create(title='經營者持股比例', selections='無,>5%,>4%,>3%,2%,>1%', variable_column='DirectorSupervisorShareRatio', usage='not_often')
#     FilterCondition.objects.create(title='股利發放率', selections='無,<60%,<50%,<40%,<30%,<20%,<10%', variable_column='DividendPayoutRatio', usage='not_often')

# def master_filter_conditions():
#     master_filter_conditions = UserFilterCondition()
#     master_filter_conditions.Master = '巴菲特'
#     master_filter_conditions.MarketValue = '>100億'
#     master_filter_conditions.GrossMargin = '>20%'
#     master_filter_conditions.ReturnOfEquity = '>15%'
#     master_filter_conditions.Yield = '>3%'
#     master_filter_conditions.EPS = '>0'
#     master_filter_conditions.EPSGrowthRate5Years = '>5%'
#     master_filter_conditions.EPSGrowthRate1Year = '>0%'
#     master_filter_conditions.user = User.objects.get(email='admin@mysite.com')
#     master_filter_conditions.save()

#     master_filter_conditions = UserFilterCondition()
#     master_filter_conditions.Master = '彼得林區'
#     master_filter_conditions.MarketValue = '>50億'
#     master_filter_conditions.ReturnOfAssets = '>5%'
#     master_filter_conditions.PriceEarningRatio = '<20'
#     master_filter_conditions.EPSGrowthRate1Year = '>20%'
#     master_filter_conditions.DebtAssetRatio = '<30%'
#     master_filter_conditions.user = User.objects.get(email='admin@mysite.com')
#     master_filter_conditions.save()

# def interest_rate_history():
#     # InterestRate.objects.create(date=datetime.strptime("2001-01-01", "%Y-%m-%d"), rate=3.750)
#     module_dir = os.path.dirname(__file__)
#     file_path = os.path.join(module_dir, 'interest_rate.csv')

#     with open(file_path, newline='') as csvfile:
#         # 讀取 CSV 檔案內容
#         rows = csv.reader(csvfile)

#         # 以迴圈輸出每一列
#         for row in rows:
#             date_string = str(int(row[0])+ 191100)+'01'
#             print(date_string)
#             InterestRate.objects.create(date=datetime.strptime(date_string, "%Y%m%d"), rate=float(row[1]))
#             # print(row)