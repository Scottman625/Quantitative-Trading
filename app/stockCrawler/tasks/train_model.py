import os

import tensorflow as tf
from tensorflow import keras
import pandas as pd
import datetime
print(tf.version)
from stockCore.models import User,Stock ,StockRecord ,StockDayRecommend ,KbarsType

def train_model():
    date = datetime.date(2023,1,11)
    stocks = Stock.objects.all()
    train_stock_list = []
    test_stock_list = []
    columns = []
    for x in range(19,-1,-1):
        columns.extend(['DayHigh_last_' + str(x),'DayLow_last_' + str(x),'OpeningPrice_last_' + str(x),'ClosingPrice_last_' + str(x),'MACD_last_' + str(x)])
    for stock in stocks:
        stockRecords = StockRecord.objects.filter(stock=stock,MACD__isnull=False,date__lte=datetime.date(2022,10,31)).order_by('date')
        stockRecords_list = list(stockRecords)
        for i in range(len(stockRecords_list)-20):
            item_column = []
            for x in range(19,-1,-1):
                item_column.extend([float(stockRecords_list[i+19-x].DayHigh),float(stockRecords_list[i+19-x].DayLow),float(stockRecords_list[i+19-x].OpeningPrice),float(stockRecords_list[i+19-x].ClosingPrice),float(stockRecords_list[i+19-x].MACD)])
            item_column.append(stockRecords_list[i].Signal)
            train_stock_list.append(item_column)

    for stock in stocks:
        stockRecords = StockRecord.objects.filter(stock=stock,MACD__isnull=False,date__gt=datetime.date(2022,10,31),date__lt=date).order_by('date')
        stockRecords_list = list(stockRecords)
        for i in range(len(stockRecords_list)-20):
            item_column = []
            for x in range(19,-1,-1):
                item_column.extend([float(stockRecords_list[i+19-x].DayHigh),float(stockRecords_list[i+19-x].DayLow),float(stockRecords_list[i+19-x].OpeningPrice),float(stockRecords_list[i+19-x].ClosingPrice),float(stockRecords_list[i+19-x].MACD)])

            item_column.append(stockRecords_list[i].Signal)
            test_stock_list.append(item_column)
    columns.append('Signal')
    print(columns)
    row=len(test_stock_list)
    column=len(test_stock_list[0])
    print(test_stock_list[0] , type(test_stock_list[0]))
    print(f'Rows:{row}, Column:{column}')
    print("Shape of a list:",len(test_stock_list))
    df_train = pd.DataFrame (train_stock_list, columns = columns)
    df_test = pd.DataFrame (test_stock_list, columns = columns)

    print(df_train.head)
    y_train = df_train.pop('Signal')
    y_test = df_test.pop('Signal')
    print (df_test)
    columns.remove('Signal')
    print(columns)

    feature_columns = []
    NUMERIC_COLUMNS = columns
    for feature_name in NUMERIC_COLUMNS:
        feature_columns.append(tf.feature_column.numeric_column(feature_name, dtype=tf.float32))

    print(feature_columns)

    def make_input_fn(data_df, label_df, num_epochs=10, shuffle=True, batch_size=32):
        def input_function():  # inner function, this will be returned
            ds = tf.data.Dataset.from_tensor_slices((dict(data_df), label_df))  # create tf.data.Dataset object with data and its label
            if shuffle:
                ds = ds.shuffle(1000)  # randomize order of data
            ds = ds.batch(batch_size).repeat(num_epochs)  # split dataset into batches of 32 and repeat process for number of epochs
            return ds  # return a batch of the dataset
        return input_function  # return a function object for use

    train_input_fn = make_input_fn(df_train, y_train)  # here we will call the input_function that was returned to us to get a dataset object we can feed to the model
    test_input_fn = make_input_fn(df_test, y_test, num_epochs=1, shuffle=False)

    linear_est = tf.estimator.LinearClassifier(feature_columns=feature_columns)

    linear_est.train(train_input_fn)  # train
    result = linear_est.evaluate(test_input_fn)  # get model metrics/stats by testing on tetsing data

    # clear_output()  # clears consoke output
    print(result['accuracy'])