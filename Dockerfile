# Bank churn prediction API — pickle-backed FastAPI service
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements-prod.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       g++ \
       gfortran \
       libopenblas-dev \
       liblapack-dev \
       pkg-config \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements-prod.txt

# Application code
COPY src/ ./src/

# Pickle model artifacts (preprocessor.pkl + model.pkl)
COPY artifacts/ ./artifacts/

EXPOSE 8000

CMD ["uvicorn", "churn_api.main:app", "--host", "0.0.0.0", "--port", "8000"]