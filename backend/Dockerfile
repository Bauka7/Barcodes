FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# DejaVuSans font for PDF labels is bundled in the repo
# (backend/assets/fonts/DejaVuSans.ttf) and copied below via COPY . .,
# so installing fonts-dejavu-core via apt is not needed and the build
# does not depend on Debian mirrors.

# Make pip resilient to flaky/slow networks (more retries, long timeout).
ENV PIP_DEFAULT_TIMEOUT=120
ENV PIP_RETRIES=10

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
