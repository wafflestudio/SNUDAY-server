FROM python:3.8.5
LABEL maintainer="heka1024@wafflestudio.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /root

ADD . .

RUN pip install -r ./requirements.txt
RUN python manage.py migrate

