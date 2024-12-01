FROM python:3.8-slim

RUN mkdir -p /app/data
RUN apt-get update
RUN pip install --upgrade pip
RUN pip install discord.py torch transformers

COPY bot.py /app/bot.py
COPY ollama.py /app/ollama.py

WORKDIR /app

ENTRYPOINT [ "python", "-u", "/app/bot.py" ]
