FROM python:3.9.6
LABEL maintainer="heka1024@wafflestudio.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /root

ADD ./requirements.txt .
RUN pip install -r ./requirements.txt

ADD . .

CMD "python manage.py runserver"