# Собираем React
FROM node:18-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Финальный образ с Python + статика
FROM python:3.11-slim
WORKDIR /app

# Python зависимости
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Backend код
COPY backend/ ./

# React статика - копируем правильно!
# build/ содержит: index.html, static/, manifest.json, etc.
COPY --from=frontend /app/build ./static

# Для отладки - показываем что скопировалось
RUN ls -la ./static/
RUN ls -la ./static/static/ || echo "No static/static directory"

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]