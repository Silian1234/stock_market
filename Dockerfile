FROM python:3.11-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py /app/
COPY ./core /app/core
COPY ./market /app/market
COPY ./stock_market /app/stock_market

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
