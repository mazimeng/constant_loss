FROM python:3.7-slim-stretch

WORKDIR /project

COPY requirements.txt /project/requirements.txt
RUN pip install -r requirements.txt
