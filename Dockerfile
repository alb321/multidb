FROM python:3.11-slim

WORKDIR /app

RUN apt update && \
    apt install -y binutils && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .