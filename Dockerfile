# Dockerfile for Django with Python 3.12
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/code
WORKDIR $APP_HOME

# Install system dependencies including Playwright dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc vim \
    # Playwright dependencies
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxkbcommon-dev \
    libgbm-dev \
    libasound2-dev \
    libxrandr2 \
    libxss1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    xvfb \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt $APP_HOME/
RUN pip install --upgrade pip && \
    pip install gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the project files
COPY . $APP_HOME/
RUN chmod +x $APP_HOME/entrypoint.sh

ENTRYPOINT ["sh", "/code/entrypoint.sh"]