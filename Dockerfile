FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y build-essential libpq-dev libpq5 && rm -rf /var/lib/apt/lists/* && apt-get clean

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS final

RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/* && apt-get clean

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./app .