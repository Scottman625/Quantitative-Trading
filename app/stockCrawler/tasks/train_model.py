from stockCore.models import User, Stock, StockRecord, StockDayRecommend, KbarsType
import os

import tensorflow as tf
from tensorflow import keras
from keras.utils import FeatureSpace
import pandas as pd
import datetime
print(tf.version)


def train_model():
    date = datetime.date(2023, 3, 10)
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

                item_column.extend([float(stockRecords_list[i+19-x].DayHigh), float(stockRecords_list[i+19-x].DayLow), float(
                    stockRecords_list[i+19-x].OpeningPrice), float(stockRecords_list[i+19-x].ClosingPrice), float(stockRecords_list[i+19-x].MACD)])
            item_column.append(stockRecords_list[i].Signal)
            val_list.append(item_column)
            predict_data_list.append(item_column)

    print(predict_data_list[0])
    print(len(predict_data_list))
    # for stock in stocks:
    #     stockRecords = StockRecord.objects.filter(stock=stock,MACD__isnull=False,date__gt=datetime.date(2022,10,31),date__lt=date).order_by('date')
    #     stockRecords_list = list(stockRecords)
    #     for i in range(len(stockRecords_list)-20):
    #         item_column = []
    #         for x in range(19,-1,-1):
    #             item_column.extend([float(stockRecords_list[i+19-x].DayHigh),float(stockRecords_list[i+19-x].DayLow),float(stockRecords_list[i+19-x].OpeningPrice),float(stockRecords_list[i+19-x].ClosingPrice),float(stockRecords_list[i+19-x].MACD)])

    # item_column.append(stockRecords_list[i].Signal)
    # test_stock_list.append(item_column)
    columns.append('Signal')

    dataframe = pd.DataFrame(val_list, columns=columns)
    df_test = dataframe.sample(frac=0.2, random_state=1337)
    df_train = dataframe.drop(df_test.index)

    def dataframe_to_dataset(dataframe):
        dataframe = dataframe.copy()
        labels = dataframe.pop("Signal")
        ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
        ds = ds.shuffle(buffer_size=len(dataframe))
        return ds

    train_ds = dataframe_to_dataset(df_train)
    val_ds = dataframe_to_dataset(df_test)

    train_ds = train_ds.batch(32)
    val_ds = val_ds.batch(32)

    feature_dict = {}

    for item in columns:
        feature_dict[item] = "float_normalized"

    print(feature_dict)
    feature_space = FeatureSpace(
        features=feature_dict,
        # We create additional features by hashing
        # value co-occurrences for the
        # following groups of categorical features.
        # crosses=[("sex", "age"), ("thal", "ca")],
        # The hashing space for these co-occurrences
        # wil be 32-dimensional.
        # crossing_dim=32,
        # Our utility will one-hot encode all categorical
        # features and concat all features into a single
        # vector (one vector per sample).
        output_mode="concat",
    )

    train_ds_with_no_labels = train_ds.map(lambda x, _: x)
    feature_space.adapt(train_ds_with_no_labels)

    for x, _ in train_ds.take(1):
        preprocessed_x = feature_space(x)
        print("preprocessed_x.shape:", preprocessed_x.shape)
        print("preprocessed_x.dtype:", preprocessed_x.dtype)

    # preprocessed_train_ds = train_ds.map(
    #     lambda x, y: (feature_space(x), y), num_parallel_calls=tf.data.AUTOTUNE
    # )
    # preprocessed_train_ds = preprocessed_train_ds.prefetch(tf.data.AUTOTUNE)

    # preprocessed_val_ds = val_ds.map(
    #     lambda x, y: (feature_space(x), y), num_parallel_calls=tf.data.AUTOTUNE
    # )
    # preprocessed_val_ds = preprocessed_val_ds.prefetch(tf.data.AUTOTUNE)

    # dict_inputs = feature_space.get_inputs()

    # encoded_features = feature_space.get_encoded_features()

    # x = keras.layers.Dense(32, activation="relu")(encoded_features)
    # x = keras.layers.Dropout(0.5)(x)
    # predictions = keras.layers.Dense(1, activation="sigmoid")(x)

    # training_model = keras.Model(inputs=encoded_features, outputs=predictions)
    # training_model.compile(
    #     optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
    # )

    # inference_model = keras.Model(inputs=dict_inputs, outputs=predictions)

    # training_model.fit(
    #     preprocessed_train_ds, epochs=20, validation_data=preprocessed_val_ds, verbose=2
    # )

    # for predict_data in predict_data_list:

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