from django.contrib import admin
from .models import Stock, StockRecord, User ,StockDayRecommend ,UserStock ,UserStockTrade
from .models import Index,Category ,KbarsType


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id','stock_code', 'name', 'stockIndustry', 'stockMoneyDJIntroduceURL')

@admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    list_display = ('id','date', 'stock','OpeningPrice','ClosingPrice')
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')

@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name','index')

@admin.register(KbarsType)
class KbarsTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name')

@admin.register(StockDayRecommend)
class StockDayRecommendAdmin(admin.ModelAdmin):
    list_display = ('id','stock','date','type')

@admin.register(UserStock)
class UserStockAdmin(admin.ModelAdmin):
    list_display = ('id','user','stock','bid_price','bid_volume','amount')

@admin.register(UserStockTrade)
class UserStockTradeAdmin(admin.ModelAdmin):
    list_display = ('id','userstock','sell_price','sell_volume','profit')
