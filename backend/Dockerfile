FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Шрифт DejaVuSans для PDF-наклеек вшит в репозиторий
# (backend/assets/fonts/DejaVuSans.ttf) и копируется ниже через COPY . .,
# поэтому установка fonts-dejavu-core через apt не нужна — сборка не зависит
# от доступности Debian-зеркал.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
