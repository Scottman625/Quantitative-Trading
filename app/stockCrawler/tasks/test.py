import shioaji as sj # 載入永豐金Python API
import pandas as pd
from datetime import date, timedelta

sj.__version__ # 版本為 "0.3.6.dev3"
api = sj.Shioaji(simulation=False) # simulation=False 即表示使用正式環境
PERSON_ID = "D122776936" #身分證字號
PASSWORD = "Scott0815" #密碼
api.login(PERSON_ID, PASSWORD) # 登入

start_date = '2022-01-01'
end_date = '20' + date.today().strftime("%y-%m-%d")
kbars =api.kbars(contract=api.Contracts.Stocks['6689'], start = start_date , end = end_date )

#轉成dataframe
df = pd.DataFrame({**kbars})
df.ts = pd.to_datetime(df.ts)
# df
#分K轉成日K
df.set_index(df.ts,inplace=True)
df = df.resample('D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume':'sum'})
df.dropna(inplace=True)

# print(type(df.iloc[-1].name.date()))
for index, row in df.iterrows():

    print(type(row.Open))

# for index in df:
#     print(index)