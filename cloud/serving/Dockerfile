# AGNI-ASR gateway — CPU-first image (CUDA picked up automatically when present)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY cloud/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# contextual layout: /app/serving, /app/configs; edge model mounted at runtime
COPY cloud/serving ./serving
COPY cloud/configs ./configs

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["python", "-m", "uvicorn", "serving.api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
