FROM --platform=linux/arm64/v8 sinotrade/shioaji:0.3.4.dev6
# LABEL maintainer twtrubiks
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
# 更新 pip
# RUN apt-get update
# RUN apt-get -y install python3-pip
RUN pip install pip -U
# 将 requirements.txt 复制到容器的 code 目录
ADD requirements.txt /code/
# 安装库
RUN pip install -r requirements.txt

RUN pip install https://storage.googleapis.com/tensorflow/mac/cpu/tensorflow-1.9.0-py3-none-any.whl
# 将当前目录复制到容器的 code 目录
ADD . /code/

# CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
# RUN apt-get install rabbitmq-server -y --fix-missing 
# RUN service rabbitmq-server start
