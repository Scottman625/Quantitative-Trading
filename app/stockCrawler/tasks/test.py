from stockCore.models import KeyValueIndex, FilterCondition, UserFilterCondition, User, InterestRate, Stock

stock = Stock.objects.get(id=1)
print(stock)