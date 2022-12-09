from email.policy import default
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.urls import reverse
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db.models import Avg ,Sum 
import decimal

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        # user = self.model(email=self.normalize_email(email), **extra_fields)
        user = self.model(
            email=self.normalize_email(email), 
            name=extra_fields.get('name'),
            fb_id=extra_fields.get('fb_id'),
            google_id=extra_fields.get('google_id'),
            apple_id=extra_fields.get('apple_id'),
            line_id=extra_fields.get('line_id')
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        """Creates and saves a new super user"""
        user = self.create_user(email, password, **extra_fields)

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that suppors using email instead of username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    fb_id = models.CharField(max_length=255, default='', blank = True, null=True)
    google_id = models.CharField(max_length=255, default='', blank = True, null=True)
    apple_id = models.CharField(max_length=255, default='', blank = True, null=True)
    line_id = models.CharField(max_length=255, default='', blank = True, null=True)

    USERNAME_FIELD = 'email'

class Index(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    index = models.ForeignKey(
        Index,
        null=True,
        on_delete=models.SET_NULL
    )
    avgPEStr = models.CharField(max_length=255, default='')
    avgMarketValueStr = models.CharField(max_length=255, default='')
    avgYieldStr = models.CharField(max_length=255, default='')
    avgROEStr = models.CharField(max_length=255, default='')
    avgEPSStr = models.CharField(max_length=255, default='')
    avgGrossMarginStr = models.CharField(max_length=255, default='')
    avgDebtAssetRatioStr = models.CharField(max_length=255, default='')
    avgEPSGrowthRate5YearsStr = models.CharField(max_length=255, default='')


    def __str__(self):
        return self.name

class Stock(models.Model):
    stock_code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        null=True,
        on_delete=models.SET_NULL
    )

    stockIndustry = models.CharField(max_length=255,default='')
    stockFullName = models.CharField(max_length=255,default='')
    stockAddress = models.CharField(max_length=255,default='')
    stockChairman = models.CharField(max_length=255,default='')
    stockManager = models.CharField(max_length=255,default='')
    stockMainBusiness = models.TextField(default='')
    stockCreatedDate = models.CharField(max_length=255,default='')
    stockCapital = models.CharField(max_length=255,default='')
    stockIPODate = models.CharField(max_length=255,default='')
    stockState = models.CharField(max_length=255,default='')
    stockCommonSharePrice = models.CharField(max_length=255,default='')
    stockCommonShares = models.CharField(max_length=255,default='')
    stockDividendFrequency = models.CharField(max_length=255,default='', null=True)
    stockCompanyURL = models.CharField(max_length=255,default='', null=True)
    stockMoneyDJIntroduceURL = models.CharField(max_length=255,default='', null=True)
    stockCompanyIntroduceURL = models.CharField(max_length=255,default='', null=True)
    stockConpanyInvestorURL = models.CharField(max_length=255,default='', null=True)
    stockCompanyAnnualReportURL = models.CharField(max_length=255,default='', null=True)
    stockCompanySeasonFinancialReportURL = models.CharField(max_length=255,default='', null=True)

    financialReportStartDate = models.CharField(max_length=255,default='')
    annualReportStartDate = models.CharField(max_length=255,default='')

    def __str__(self):
        return self.name

class StockRecord(models.Model):

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
    )

    date = models.DateField(auto_now=False)

    OpeningPrice = models.DecimalField(max_digits=7, decimal_places=2)
    ClosingPrice = models.DecimalField(max_digits=7, decimal_places=2)
    DayHigh = models.DecimalField(max_digits=7, decimal_places=2)
    DayLow = models.DecimalField(max_digits=7, decimal_places=2)

    MA_s = models.DecimalField(max_digits=7, decimal_places=2,null=True,blank=True)
    MA_m = models.DecimalField(max_digits=7, decimal_places=2,null=True,blank=True)
    MA_l = models.DecimalField(max_digits=7, decimal_places=2,null=True,blank=True)

    #交易股數
    Volume = models.DecimalField(max_digits=13, decimal_places=0)

    @property
    def MA_5(self):
        
        ma_5 = StockRecord.objects.filter(stock=self.stock,date__lte=self.date).order_by('-date')[:5].aggregate(Avg('ClosingPrice'))['ClosingPrice__avg']
        digit = len(str(self.ClosingPrice).split('.')[1])
        return round(decimal.Decimal(str(ma_5)), digit)

    @property
    def MA_10(self):
        ma_10 = StockRecord.objects.filter(stock=self.stock,date__lte=self.date).order_by('-date')[:10].aggregate(Avg('ClosingPrice'))['ClosingPrice__avg']
        digit = len(str(self.ClosingPrice).split('.')[1])
        return round(decimal.Decimal(str(ma_10)), digit)

    @property
    def MA_20(self):
        ma_20 = StockRecord.objects.filter(stock=self.stock,date__lte=self.date).order_by('-date')[:20].aggregate(Avg('ClosingPrice'))['ClosingPrice__avg']
        digit = len(str(self.ClosingPrice).split('.')[1])
        return round(decimal.Decimal(str(ma_20)), digit)

class KbarsType(models.Model):
    Kbars_Type = [
        ('1', 'ChildParent'),
        ('2', 'LongShadeLine'),
    ]
    name = models.CharField(max_length=100, choices=Kbars_Type,null=True,blank=True)
    def __str__(self):
        return self.name

class StockDayRecommend(models.Model):

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
    )

    date = models.DateField(auto_now=False)

    type = models.ForeignKey(
        KbarsType,
        on_delete=models.CASCADE,
    )

class UserStock(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
    )

    buy_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    bid_volume = models.DecimalField(max_digits=13, decimal_places=0)

    amount = models.IntegerField(default=0,null=True)

    bid_price = models.DecimalField(max_digits=7, decimal_places=2)

    cost = models.DecimalField(max_digits=13, decimal_places=2)

    is_cover = models.BooleanField(default=False)

    profit = models.DecimalField(max_digits=13, decimal_places=2)


class UserStockTrade(models.Model):

    userstock = models.ForeignKey(
        UserStock,
        on_delete=models.CASCADE,
    )

    sell_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    sell_volume = models.DecimalField(max_digits=13, decimal_places=0)

    # amount = models.IntegerField(default=0,null=True)

    sell_money = models.DecimalField(max_digits=7, decimal_places=2)

    sell_price = models.DecimalField(max_digits=13, decimal_places=2)

    profit = models.DecimalField(max_digits=13, decimal_places=2)