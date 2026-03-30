FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app

# store downloaded browsers in a path shared with non-root user
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# install system dependencies for Playwright browsers and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libssl-dev libffi-dev curl \
    # Playwright browser dependencies
    libglib2.0-0 \
    libgobject-2.0-0 \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libexpat1 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    # Additional dependencies for pdf2image and pytesseract
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with system dependencies BEFORE switching to non-root user
RUN playwright install --with-deps chromium
RUN chown -R root:root ${PLAYWRIGHT_BROWSERS_PATH}

# create a non-root user and set ownership
RUN groupadd -r app && useradd -r -g app -d /home/app -m app \
    && chown -R app:app /app \
    && chown -R app:app ${PLAYWRIGHT_BROWSERS_PATH}

# ensure runtime directories exist for Chromium / Playwright
RUN mkdir -p /home/app/.cache /home/app/.config \
    && chown -R app:app /home/app/.cache /home/app/.config

USER app

COPY --chown=app:app . .

# Informational only — Cloud Run controls the actual port via $PORT
EXPOSE 8000

# Use shell form to support dual-mode execution (API vs Worker)
CMD ["sh", "-c", "if [ \"$MODE\" = \"WORKER\" ]; then python worker.py; else uvicorn main.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 0; fi"]