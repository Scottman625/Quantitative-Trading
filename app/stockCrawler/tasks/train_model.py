from stockCore.models import User, Stock, StockRecord, StockDayRecommend, KbarsType
import os

import tensorflow as tf
from tensorflow import keras
import pandas as pd
import datetime
from keras.models import Sequential
from keras.layers import Dense
from keras.models import load_model


def train_model():
    # from sklearn.model_selection import train_test_split
    date = datetime.date(2023, 1, 11)
    stocks = Stock.objects.all()
    val_list = []
    predict_data_list = []
    columns = []
    for x in range(19, -1, -1):
        columns.extend(['DayHigh_last_' + str(x), 'DayLow_last_' + str(x),
                       'OpeningPrice_last_' + str(x), 'ClosingPrice_last_' + str(x), 'MACD_last_' + str(x)])
    for stock in stocks:
        stockRecords = StockRecord.objects.filter(
            stock=stock, MACD__isnull=False, date__lte=date).order_by('date')
        stockRecords_list = list(stockRecords)
        for i in range(len(stockRecords_list)-20):
            item_column = []
            for x in range(19, -1, -1):

                # item_column.extend([float(stockRecords_list[i+19-x].DayHigh), float(stockRecords_list[i+19-x].DayLow), float(
                #     stockRecords_list[i+19-x].OpeningPrice), float(stockRecords_list[i+19-x].ClosingPrice), float(stockRecords_list[i+19-x].MACD)])
                if stockRecords_list[i+19-x].DayLow != 0 and stockRecords_list[i+19-x].DayLow != None :
                    item_column.extend([float((float(stockRecords_list[i+19-x].DayHigh)-float(stockRecords_list[i+19-x].DayLow))/float(stockRecords_list[i+19-x].DayLow))])
                else:
                    item_column.extend([0])
                if stockRecords_list[i+19-x].ClosingPrice != 0 and stockRecords_list[i+19-x].ClosingPrice != None :
                    item_column.extend([float((float(stockRecords_list[i+19-x].OpeningPrice) - float(stockRecords_list[i+19-x].ClosingPrice))/float(stockRecords_list[i+19-x].ClosingPrice))])
                else:
                    item_column.extend([0])
                item_column.extend([float(stockRecords_list[i+19-x].DIF), float(stockRecords_list[i+19-x].MACD),float(stockRecords_list[i+19-x].Volume)])
            item_column.append(stockRecords_list[i+19].Signal)
            val_list.append(item_column)
            predict_data_list.append(item_column)

    columns.append('Signal')

    dataframe = pd.DataFrame(val_list, columns=columns)
    df_test = dataframe.sample(frac=0.2, random_state=1337)
    df_train = dataframe.drop(df_test.index)

    X_train = df_train.iloc[:, :-1]
    y_train = df_train.iloc[:, -1]

    input_shape = (X_train.shape[1],)
    print(input_shape)  
    x_test = df_test.iloc[:,:-1]
    y_test = df_test.iloc[:,-1]

    # X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.2, random_state=42)


    model = Sequential()
    model.add(Dense(64, input_shape=input_shape, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print(model.summary())

    model.fit(X_train, y_train, epochs=25, batch_size=32, validation_data=(x_test, y_test))

    model.save('my_model.h5')

    score = model.evaluate(x_test, y_test)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])

    
    # print(df_train.head)
    # y_train = df_train.pop('Signal')
    # y_test = df_test.pop('Signal')
    # print(df_test)
    # columns.remove('Signal')
    # print(columns)

    # feature_columns = []
    # NUMERIC_COLUMNS = columns
    # for feature_name in NUMERIC_COLUMNS:
    #     feature_columns.append(tf.feature_column.numeric_column(
    #         feature_name, dtype=tf.float32))

    # print(feature_columns)

    # def make_input_fn(data_df, label_df, num_epochs=10, shuffle=True, batch_size=32):
    #     def input_function():  # inner function, this will be returned
    #         # create tf.data.Dataset object with data and its label
    #         ds = tf.data.Dataset.from_tensor_slices((dict(data_df), label_df))
    #         if shuffle:
    #             ds = ds.shuffle(1000)  # randomize order of data
    #         # split dataset into batches of 32 and repeat process for number of epochs
    #         ds = ds.batch(batch_size).repeat(num_epochs)
    #         return ds  # return a batch of the dataset
    #     return input_function  # return a function object for use

    # # here we will call the input_function that was returned to us to get a dataset object we can feed to the model
    # train_input_fn = make_input_fn(df_train, y_train)
    # test_input_fn = make_input_fn(df_test, y_test, num_epochs=1, shuffle=False)

    # linear_est = tf.estimator.LinearClassifier(feature_columns=feature_columns)

    # linear_est.train(train_input_fn)  # train
    # # get model metrics/stats by testing on tetsing data
    # result = linear_est.evaluate(test_input_fn)

    # # clear_output()  # clears consoke output
    # print(result['accuracy'])

def model_predict():
    import pytz
    import numpy as np
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
            for i in range(len(stockRecords_list)-20):
                item_column = []
                check_input = []
                for x in range(19, -1, -1):

                    if stockRecords_list[i+19-x].DayLow != 0 and stockRecords_list[i+19-x].DayLow != None :
                        item_column.extend([float((float(stockRecords_list[i+19-x].DayHigh)-float(stockRecords_list[i+19-x].DayLow))/float(stockRecords_list[i+19-x].DayLow))])
                    else:
                        item_column.extend([0])
                    if stockRecords_list[i+19-x].ClosingPrice != 0 and stockRecords_list[i+19-x].ClosingPrice != None :
                        item_column.extend([float((float(stockRecords_list[i+19-x].OpeningPrice) - float(stockRecords_list[i+19-x].ClosingPrice))/float(stockRecords_list[i+19-x].ClosingPrice))])
                    else:
                        item_column.extend([0])
                    item_column.extend([float(stockRecords_list[i+19-x].DIF), float(stockRecords_list[i+19-x].MACD),float(stockRecords_list[i+19-x].Volume)])
                    check_input.extend([stockRecords_list[i+19-x].stock.stock_code,stockRecords_list[i+19-x].date])
                    if x == 0:
                        check_input.extend([stock])
                # if predict_val >= 0.85:
                #     StockDayRecommend.objects.create(stock=stock,type=KbarsType.objects.get(id=5),date=stockRecords_list[i+19].date)
                #     print('stock_code:',stock.stock_code, 'stock_name:',stock.name, 'date:',stockRecords_list[i+19].date)
                predict_data_list.append(item_column)
                check_input_list.append(check_input)
    predictions = model.predict(np.array(predict_data_list))

    print(len(predictions),len(check_input_list),len(predict_data_list))
    for i in range(len(predictions)):
        if predictions[i][0] > 0.7:
            # print(predictions[i][0])
            print('Input:',check_input_list[i][-3] ,check_input_list[i][-2],check_input_list[i][-1], 'Predicted Value:', predictions[i][0])
            StockDayRecommend.objects.create(stock=check_input_list[i][-1],type=KbarsType.objects.get(id=5),date=check_input_list[i][-2])
