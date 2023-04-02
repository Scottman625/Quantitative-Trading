from stockCore.models import User, Stock, StockRecord, StockDayRecommend, KbarsType
import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import datetime
from keras.models import Sequential
from keras.layers import Dense
from keras.models import load_model

def train_model():
    # from sklearn.model_selection import train_test_split
    date = datetime.date(2023, 1, 31)
    stocks = Stock.objects.all()
    val_list = []
    y_train_list = []

    # for x in range(9, -1, -1):
    #     columns.extend(['DayHigh_last_' + str(x), 'DayLow_last_' + str(x),
    #                    'OpeningPrice_last_' + str(x), 'ClosingPrice_last_' + str(x), 'MACD_last_' + str(x)])
    for stock in stocks:
        stockRecords = StockRecord.objects.filter(
            stock=stock, MACD__isnull=False, date__lte=date).order_by('date')
        stockRecords_list = list(stockRecords)
        

        for i in range(len(stockRecords_list)-10):
            item_column = []
            for x in range(9, -1, -1):

                if stockRecords_list[i+9-x].DayLow != 0 and stockRecords_list[i+9-x].DayLow != None :
                        item_column.extend([float((float(stockRecords_list[i+9-x].DayHigh)-float(stockRecords_list[i+9-x].DayLow))/float(stockRecords_list[i+9-x].DayLow))])
                else:
                    item_column.extend([0])
                if stockRecords_list[i+9-x].ClosingPrice != 0 and stockRecords_list[i+9-x].ClosingPrice != None :
                    item_column.extend([float((float(stockRecords_list[i+9-x].OpeningPrice) - float(stockRecords_list[i+9-x].ClosingPrice))/float(stockRecords_list[i+9-x].ClosingPrice))])
                else:
                    item_column.extend([0])
                if float(stockRecords_list[i+9-x].EMA_26) != 0 and float(stockRecords_list[i+9-x].EMA_26) != None:
                    item_column.extend([(float(stockRecords_list[i+9-x].DIF)-float(stockRecords_list[i+9-x].EMA_26))/float(stockRecords_list[i+9-x].EMA_26)])  
                else:
                    item_column.extend([0])             
                item_column.extend([float(stockRecords_list[i+9-x].MACD)])
                item_column.extend([float(stockRecords_list[i+9-x].OSC)])

            
            y_train_list.append(stockRecords_list[i+9].Signal)

            val_list.append(item_column)

    # columns.append('Signal')

    # dataframe = pd.DataFrame(val_list, columns=columns)
    # df_test = dataframe.sample(frac=0.2, random_state=1337)
    # df_train = dataframe.drop(df_test.index)

    # X_train = df_train.iloc[:, :-1]
    # y_train = df_train.iloc[:, -1]


    X_train = np.array(val_list)
    y_train = np.array(y_train_list)


    # print(y_train)
    input_shape = X_train.shape[1:]
    print(input_shape)  
    # x_test = df_test.iloc[:,:-1]
    # y_test = df_test.iloc[:,-1]

    # X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.2, random_state=42)


    model = Sequential()
    model.add(Dense(64, input_shape=input_shape, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(units = 1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print(model.summary())

    model.fit(X_train, y_train, epochs=30, batch_size=32, validation_split=0.1,shuffle=True,verbose=2)

    model.save('my_model.h5')

    # score = model.evaluate(x_test, y_test)
    # print('Test loss:', score[0])
    # print('Test accuracy:', score[1])


def model_predict():
    import pytz
    from datetime import date, datetime, timedelta, timezone
    tw = pytz.timezone('Asia/Taipei')
    twdt = tw.localize(datetime.now())
    model = load_model('my_model.h5')
    predict_data_list = []
    check_input_list = []
    date = (twdt.date() - timedelta(days=60)).strftime("%Y-%m-%d")
    stocks = Stock.objects.all()
    for stock in stocks:
        # if StockRecord.objects.filter(
        #     stock=stock, MACD__isnull=False, date__gt=(twdt.date() - timedelta(days=1)).strftime("%Y-%m-%d")).count() != 0:
            stockRecords = StockRecord.objects.filter(stock=stock, MACD__isnull=False, date__gte=date).order_by('date')
            stockRecords_list = list(stockRecords)
            for i in range(len(stockRecords_list)-10):
                item_column = []
                check_input = []
                for x in range(9, -1, -1):

                    if stockRecords_list[i+9-x].DayLow != 0 and stockRecords_list[i+9-x].DayLow != None :
                        item_column.extend([float((float(stockRecords_list[i+9-x].DayHigh)-float(stockRecords_list[i+9-x].DayLow))/float(stockRecords_list[i+9-x].DayLow))])
                    else:
                        item_column.extend([0])
                    if stockRecords_list[i+9-x].ClosingPrice != 0 and stockRecords_list[i+9-x].ClosingPrice != None :
                        item_column.extend([float((float(stockRecords_list[i+9-x].OpeningPrice) - float(stockRecords_list[i+9-x].ClosingPrice))/float(stockRecords_list[i+9-x].ClosingPrice))])
                    else:
                        item_column.extend([0])
                    if float(stockRecords_list[i+9-x].EMA_26) != 0 and float(stockRecords_list[i+9-x].EMA_26) != None:
                        item_column.extend([(float(stockRecords_list[i+9-x].DIF)-float(stockRecords_list[i+9-x].EMA_26))/float(stockRecords_list[i+9-x].EMA_26)])  
                    else:
                        item_column.extend([0])             
                    item_column.extend([float(stockRecords_list[i+9-x].MACD)])
                    item_column.extend([float(stockRecords_list[i+9-x].OSC)])

                    check_input.extend([stockRecords_list[i+9-x].stock.stock_code,stockRecords_list[i+9-x].date])
                    if x == 0:
                        check_input.extend([stock])
                # if predict_val >= 0.85:
                #     StockDayRecommend.objects.create(stock=stock,type=KbarsType.objects.get(id=5),date=stockRecords_list[i+9].date)
                #     print('stock_code:',stock.stock_code, 'stock_name:',stock.name, 'date:',stockRecords_list[i+9].date)

            
                check_input_list.append(check_input)
                predict_data_list.append(item_column)
    predictions = model.predict(np.array(predict_data_list))

    for i in range(len(predictions)):
        if predictions[i][0] > 0.55:
            # print(predictions[i][0])
            print('Input:',check_input_list[i][-3] ,check_input_list[i][-2],check_input_list[i][-1], 'Predicted Value:', predictions[i][0])
            if StockDayRecommend.objects.filter(stock=check_input_list[i][-1],type=KbarsType.objects.get(id=5),date=check_input_list[i][-2]).count() == 0:
                StockDayRecommend.objects.create(stock=check_input_list[i][-1],type=KbarsType.objects.get(id=5),date=check_input_list[i][-2])
