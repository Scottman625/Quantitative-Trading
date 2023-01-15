FROM sinotrade/shioaji:latest
# LABEL maintainer twtrubiks
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
# 更新 pip
RUN pip install pip -U
# 将 requirements.txt 复制到容器的 code 目录
ADD requirements.txt /code/
# 安装库
RUN pip install -r requirements.txt
# 将当前目录复制到容器的 code 目录
ADD . /code/

# CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
