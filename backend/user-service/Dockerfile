FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r user-service/requirements.txt

EXPOSE 8001

ENV PYTHONUNBUFFERED=1

WORKDIR /app/user-service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]