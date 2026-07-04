FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
# Cloud Run 注入 PORT；uvicorn 綁它
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
