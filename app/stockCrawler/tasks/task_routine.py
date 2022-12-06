from stockCore.models import UserFilterCondition, UserFilterdStock, User, KeyValueSheetCurrent, Category


def update_filtered_stocks(user):
    userFilterConditions = UserFilterCondition.objects.filter(user=user)
    
    for userCondition in userFilterConditions:
        userFilteredStocks = UserFilterdStock.objects.filter(user_filter_condition=userCondition)

        filter_params = get_apply_filter_params(userCondition)
        queryset = KeyValueSheetCurrent.objects.filter(**filter_params)

        # add new stock
        for keyValueSheet in queryset:
            if userFilteredStocks.filter(stock=keyValueSheet.stock).count()==0:
                newFilterdStock = UserFilterdStock(user=user, stock=keyValueSheet.stock, user_filter_condition=userCondition)
                newFilterdStock.save()

        # remove old stock
        for oldFilterdStock in  userFilteredStocks:
            if queryset.filter(stock=oldFilterdStock.stock).count()==0:
                oldFilterdStock.delete()




def get_apply_filter_params(filterCondition):
    filter_params = {}

    MarketValue = filterCondition.MarketValue
    if MarketValue != None and MarketValue != '無':
        if MarketValue == '>1000億':
            filter_params['MarketValue__gte'] = 100000000
        elif MarketValue == '>500億':
            filter_params['MarketValue__gte'] = 50000000
        elif MarketValue == '>100億':           
            filter_params['MarketValue__gte'] = 10000000
        elif MarketValue == '>50億':              
            filter_params['MarketValue__gte'] = 5000000
        elif MarketValue == '>20億':             
            filter_params['MarketValue__gte'] = 2000000
        elif MarketValue == '>10億':
            filter_params['MarketValue__gte'] = 1000000

    TheCategory = filterCondition.Category
    if TheCategory != None and TheCategory != '無':
        category = Category.objects.get(name=TheCategory)
        filter_params['category__exact'] = category

    PriceEarningRatio = filterCondition.PriceEarningRatio
    if PriceEarningRatio != None and PriceEarningRatio != '無':
        if PriceEarningRatio == '<5':
            filter_params['PriceEarningRatio__lte'] = 5
        elif PriceEarningRatio == '<10' :
            filter_params['PriceEarningRatio__lte'] = 10
        elif PriceEarningRatio == '<15':
            filter_params['PriceEarningRatio__lte'] = 15
        elif PriceEarningRatio == '<20':
            filter_params['PriceEarningRatio__lte'] = 20
        elif PriceEarningRatio == '<30':
            filter_params['PriceEarningRatio__lte'] = 30

    Yield = filterCondition.Yield
    Yield = Yield.replace('%','')
    if Yield != None and Yield != '無':
        if Yield == '>8':
            filter_params['Yield__gte'] = 8
        elif Yield == '>5':
            filter_params['Yield__gte'] = 5
        elif Yield == '>3':           
            filter_params['Yield__gte'] = 3
        elif Yield == '>2':              
            filter_params['Yield__gte'] = 2
        elif Yield == '>1':             
            filter_params['Yield__gte'] = 1
        
    EPS = filterCondition.EPS
    if EPS != None and EPS != '無':
        if EPS == '>20':
            filter_params['EPS__gte'] = 20
        elif EPS == '>15':
            filter_params['EPS__gte'] = 15
        elif EPS == '>10':           
            filter_params['EPS__gte'] = 10
        elif EPS == '>5':              
            filter_params['EPS__gte'] = 5
        elif EPS == '>0':             
            filter_params['EPS__gte'] = 0

    ReturnOfEquity = filterCondition.ReturnOfEquity
    ReturnOfEquity = ReturnOfEquity.replace('%','')
    if ReturnOfEquity != None and ReturnOfEquity != '無':
        if ReturnOfEquity == '>25':
            filter_params['ReturnOfEquity__gte'] = 25
        elif ReturnOfEquity == '>20':
            filter_params['ReturnOfEquity__gte'] = 20
        elif ReturnOfEquity == '>15':           
            filter_params['ReturnOfEquity__gte'] = 15
        elif ReturnOfEquity == '>10':              
            filter_params['ReturnOfEquity__gte'] = 10
        elif ReturnOfEquity == '>5':             
            filter_params['ReturnOfEquity__gte'] = 5
        elif ReturnOfEquity == '>0':             
            filter_params['ReturnOfEquity__gte'] = 0

    ReturnOfAssets = filterCondition.ReturnOfAssets
    ReturnOfAssets = ReturnOfAssets.replace('%','')
    if ReturnOfAssets != None and ReturnOfAssets != '無':
        if ReturnOfAssets == '>25':
            filter_params['ReturnOfAssets__gte'] = 25
        elif ReturnOfAssets == '>20':
            filter_params['ReturnOfAssets__gte'] = 20
        elif ReturnOfAssets == '>15':           
            filter_params['ReturnOfAssets__gte'] = 15
        elif ReturnOfAssets == '>10':              
            filter_params['ReturnOfAssets__gte'] = 10
        elif ReturnOfAssets == '>5':             
            filter_params['ReturnOfAssets__gte'] = 5
        elif ReturnOfAssets == '>0':             
            filter_params['ReturnOfAssets__gte'] = 0

    PriceBookRatio = filterCondition.PriceBookRatio
    if PriceBookRatio != None and PriceBookRatio != '無':
        if PriceBookRatio == '<1':
            filter_params['PriceBookRatio__lte'] = 1
        elif PriceBookRatio == '<2' :
            filter_params['PriceBookRatio__lte'] = 2
        elif PriceBookRatio == '<3':
            filter_params['PriceBookRatio__lte'] = 3
        elif PriceBookRatio == '<5':
            filter_params['PriceBookRatio__lte'] = 5
        elif PriceBookRatio == '<10':
            filter_params['PriceBookRatio__lte'] = 10
        elif PriceBookRatio == '<20':
            filter_params['PriceBookRatio__lte'] = 20

    GrossMargin = filterCondition.GrossMargin
    GrossMargin = GrossMargin.replace('%','')
    if GrossMargin != None and GrossMargin != '無':
        if GrossMargin == '>60':
            filter_params['GrossMargin__gte'] = 60
        elif GrossMargin == '>50':
            filter_params['GrossMargin__gte'] = 50
        elif GrossMargin == '>40':           
            filter_params['GrossMargin__gte'] = 40
        elif GrossMargin == '>30':              
            filter_params['GrossMargin__gte'] = 30
        elif GrossMargin == '>20':             
            filter_params['GrossMargin__gte'] = 20
        elif GrossMargin == '>10':             
            filter_params['GrossMargin__gte'] = 10
        elif GrossMargin == '>0':             
            filter_params['GrossMargin__gte'] = 0

    OperatingMargin = filterCondition.OperatingMargin
    OperatingMargin = OperatingMargin.replace('%','')
    if OperatingMargin != None and OperatingMargin != '無':
        if OperatingMargin == '>50':
            filter_params['OperatingMargin__gte'] = 50
        elif OperatingMargin == '>40':           
            filter_params['OperatingMargin__gte'] = 40
        elif OperatingMargin == '>30':              
            filter_params['OperatingMargin__gte'] = 30
        elif OperatingMargin == '>20':             
            filter_params['OperatingMargin__gte'] = 20
        elif OperatingMargin == '>10':             
            filter_params['OperatingMargin__gte'] = 10
        elif OperatingMargin == '>0':             
            filter_params['OperatingMargin__gte'] = 0


    NetProfitAfterTaxMargin = filterCondition.NetProfitAfterTaxMargin
    NetProfitAfterTaxMargin = NetProfitAfterTaxMargin.replace('%','')
    if NetProfitAfterTaxMargin != None and NetProfitAfterTaxMargin != '無':
        if NetProfitAfterTaxMargin == '>50':
            filter_params['NetProfitAfterTaxMargin__gte'] = 50
        elif NetProfitAfterTaxMargin == '>40':           
            filter_params['NetProfitAfterTaxMargin__gte'] = 40
        elif NetProfitAfterTaxMargin == '>30':              
            filter_params['NetProfitAfterTaxMargin__gte'] = 30
        elif NetProfitAfterTaxMargin == '>20':             
            filter_params['NetProfitAfterTaxMargin__gte'] = 20
        elif NetProfitAfterTaxMargin == '>10':             
            filter_params['NetProfitAfterTaxMargin__gte'] = 10
        elif NetProfitAfterTaxMargin == '>0':             
            filter_params['NetProfitAfterTaxMargin__gte'] = 0

    DebtAssetRatio = filterCondition.DebtAssetRatio
    DebtAssetRatio = DebtAssetRatio.replace('%','')
    if DebtAssetRatio != None and DebtAssetRatio != '無':
        if DebtAssetRatio == '<5':
            filter_params['DebtAssetRatio__lte'] = 5
        elif DebtAssetRatio == '<10' :
            filter_params['DebtAssetRatio__lte'] = 10
        elif DebtAssetRatio == '<15':
            filter_params['DebtAssetRatio__lte'] = 15
        elif DebtAssetRatio == '<20':
            filter_params['DebtAssetRatio__lte'] = 20
        elif DebtAssetRatio == '<25':
            filter_params['DebtAssetRatio__lte'] = 25
        elif DebtAssetRatio == '<30':
            filter_params['DebtAssetRatio__lte'] = 30
        elif DebtAssetRatio == '<40':
            filter_params['DebtAssetRatio__lte'] = 40
        elif DebtAssetRatio == '<50':
            filter_params['DebtAssetRatio__lte'] = 50

    EPSGrowthRate5Years = filterCondition.EPSGrowthRate5Years
    EPSGrowthRate5Years = EPSGrowthRate5Years.replace('%','')
    if EPSGrowthRate5Years != None and EPSGrowthRate5Years != '無':
        if EPSGrowthRate5Years == '>20':
            filter_params['EPSGrowthRate5Years__gte'] = 20
        elif EPSGrowthRate5Years == '>15':           
            filter_params['EPSGrowthRate5Years__gte'] = 15
        elif EPSGrowthRate5Years == '>10':              
            filter_params['EPSGrowthRate5Years__gte'] = 10
        elif EPSGrowthRate5Years == '>5':             
            filter_params['EPSGrowthRate5Years__gte'] = 5
        elif EPSGrowthRate5Years == '>0':             
            filter_params['EPSGrowthRate5Years__gte'] = 0

    ROEGrowthRate5Years = filterCondition.ROEGrowthRate5Years
    ROEGrowthRate5Years = ROEGrowthRate5Years.replace('%','')
    if ROEGrowthRate5Years != None and ROEGrowthRate5Years != '無':
        if ROEGrowthRate5Years == '>20':
            filter_params['ROEGrowthRate5Years__gte'] = 20
        elif ROEGrowthRate5Years == '>15':           
            filter_params['ROEGrowthRate5Years__gte'] = 15
        elif ROEGrowthRate5Years == '>10':              
            filter_params['ROEGrowthRate5Years__gte'] = 10
        elif ROEGrowthRate5Years == '>5':             
            filter_params['ROEGrowthRate5Years__gte'] = 5
        elif ROEGrowthRate5Years == '>0':             
            filter_params['ROEGrowthRate5Years__gte'] = 0

    RevenueGrowthRate5Years = filterCondition.RevenueGrowthRate5Years
    RevenueGrowthRate5Years = RevenueGrowthRate5Years.replace('%','')
    if RevenueGrowthRate5Years != None and RevenueGrowthRate5Years != '無':
        if RevenueGrowthRate5Years == '>20':
            filter_params['RevenueGrowthRate5Years__gte'] = 20
        elif RevenueGrowthRate5Years == '>15':           
            filter_params['RevenueGrowthRate5Years__gte'] = 15
        elif RevenueGrowthRate5Years == '>10':              
            filter_params['RevenueGrowthRate5Years__gte'] = 10
        elif RevenueGrowthRate5Years == '>5':             
            filter_params['RevenueGrowthRate5Years__gte'] = 5
        elif RevenueGrowthRate5Years == '>0':             
            filter_params['RevenueGrowthRate5Years__gte'] = 0

    EPSGrowthRate1Year = filterCondition.EPSGrowthRate1Year
    EPSGrowthRate1Year = EPSGrowthRate1Year.replace('%','')
    if EPSGrowthRate1Year != None and EPSGrowthRate1Year != '無':
        if EPSGrowthRate1Year == '>30':
            filter_params['EPSGrowthRate1Year__gte'] = 30
        elif EPSGrowthRate1Year == '>20':
            filter_params['EPSGrowthRate1Year__gte'] = 20
        elif EPSGrowthRate1Year == '>15':           
            filter_params['EPSGrowthRate1Year__gte'] = 15
        elif EPSGrowthRate1Year == '>10':              
            filter_params['EPSGrowthRate1Year__gte'] = 10
        elif EPSGrowthRate1Year == '>5':             
            filter_params['EPSGrowthRate1Year__gte'] = 5
        elif EPSGrowthRate1Year == '>0':             
            filter_params['EPSGrowthRate1Year__gte'] = 0
    
    ROEGrowthRate1Year = filterCondition.ROEGrowthRate1Year
    ROEGrowthRate1Year = ROEGrowthRate1Year.replace('%','')
    if ROEGrowthRate1Year != None and ROEGrowthRate1Year != '無':
        if ROEGrowthRate1Year == '>30':
            filter_params['ROEGrowthRate1Year__gte'] = 30
        elif ROEGrowthRate1Year == '>20':
            filter_params['ROEGrowthRate1Year__gte'] = 20
        elif ROEGrowthRate1Year == '>15':           
            filter_params['ROEGrowthRate1Year__gte'] = 15
        elif ROEGrowthRate1Year == '>10':              
            filter_params['ROEGrowthRate1Year__gte'] = 10
        elif ROEGrowthRate1Year == '>5':             
            filter_params['ROEGrowthRate1Year__gte'] = 5
        elif ROEGrowthRate1Year == '>0':             
            filter_params['ROEGrowthRate1Year__gte'] = 0

    RevenueGrowthRate1Year = filterCondition.RevenueGrowthRate1Year
    RevenueGrowthRate1Year = RevenueGrowthRate1Year.replace('%','')
    if RevenueGrowthRate1Year != None and RevenueGrowthRate1Year != '無':
        if RevenueGrowthRate1Year == '>30':
            filter_params['RevenueGrowthRate1Year__gte'] = 30
        elif RevenueGrowthRate1Year == '>20':
            filter_params['RevenueGrowthRate1Year__gte'] = 20
        elif RevenueGrowthRate1Year == '>15':           
            filter_params['RevenueGrowthRate1Year__gte'] = 15
        elif RevenueGrowthRate1Year == '>10':              
            filter_params['RevenueGrowthRate1Year__gte'] = 10
        elif RevenueGrowthRate1Year == '>5':             
            filter_params['RevenueGrowthRate1Year__gte'] = 5
        elif RevenueGrowthRate1Year == '>0':             
            filter_params['RevenueGrowthRate1Year__gte'] = 0

    NetProfitBeforeTaxMargin = filterCondition.NetProfitBeforeTaxMargin
    NetProfitBeforeTaxMargin = NetProfitBeforeTaxMargin.replace('%','')
    if NetProfitBeforeTaxMargin != None and NetProfitBeforeTaxMargin != '無':
        if NetProfitBeforeTaxMargin == '>60':
            filter_params['NetProfitBeforeTaxMargin__gte'] = 60
        elif NetProfitBeforeTaxMargin == '>50':
            filter_params['NetProfitBeforeTaxMargin__gte'] = 50
        elif NetProfitBeforeTaxMargin == '>40':           
            filter_params['NetProfitBeforeTaxMargin__gte'] = 40
        elif NetProfitBeforeTaxMargin == '>30':              
            filter_params['NetProfitBeforeTaxMargin__gte'] = 30
        elif NetProfitBeforeTaxMargin == '>20':             
            filter_params['NetProfitBeforeTaxMargin__gte'] = 20
        elif NetProfitBeforeTaxMargin == '>10':             
            filter_params['NetProfitBeforeTaxMargin__gte'] = 10
        elif NetProfitBeforeTaxMargin == '>0':             
            filter_params['NetProfitBeforeTaxMargin__gte'] = 0

    DirectorSupervisorShareRatio = filterCondition.DirectorSupervisorShareRatio
    DirectorSupervisorShareRatio = DirectorSupervisorShareRatio.replace('%','')
    if DirectorSupervisorShareRatio != None and DirectorSupervisorShareRatio != '無':
        if DirectorSupervisorShareRatio == '>5':
            filter_params['DirectorSupervisorShareRatio__gte'] = 5
        elif DirectorSupervisorShareRatio == '>4':
            filter_params['DirectorSupervisorShareRatio__gte'] = 4
        elif DirectorSupervisorShareRatio == '>3':           
            filter_params['DirectorSupervisorShareRatio__gte'] = 3
        elif DirectorSupervisorShareRatio == '>2':              
            filter_params['DirectorSupervisorShareRatio__gte'] = 2
        elif DirectorSupervisorShareRatio == '>1':             
            filter_params['DirectorSupervisorShareRatio__gte'] = 1

    DividendPayoutRatio = filterCondition.DividendPayoutRatio
    DividendPayoutRatio = DividendPayoutRatio.replace('%','')
    if DividendPayoutRatio != None and DividendPayoutRatio != '無':
        if DividendPayoutRatio == '>60':
            filter_params['DividendPayoutRatio__lte'] = 60
        elif DividendPayoutRatio == '>50':
            filter_params['DividendPayoutRatio__lte'] = 50
        elif DividendPayoutRatio == '>40':           
            filter_params['DividendPayoutRatio__lte'] = 40
        elif DividendPayoutRatio == '>30':              
            filter_params['DividendPayoutRatio__lte'] = 30
        elif DividendPayoutRatio == '>20':             
            filter_params['DividendPayoutRatio__lte'] = 20
        elif DividendPayoutRatio == '>10':             
            filter_params['DividendPayoutRatio__lte'] = 10
    
    return filter_params