FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
MAINTAINER wenzehua <wzh486@outlook.com>

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone
RUN pip config set global.index-url https://mirror.sjtu.edu.cn/pypi/web/simple

RUN apt-get update && apt-get install -y vim

COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

COPY . /data/app
WORKDIR /data/app

EXPOSE 8000
