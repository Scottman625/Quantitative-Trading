from django.contrib import admin
from .models import Stock, StockRecord, User
from .models import Index,Category


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
