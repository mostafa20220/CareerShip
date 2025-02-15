# Dockerfile for Django with Python 3.12
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/code
WORKDIR $APP_HOME
# Set work directory

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc vim


# Install Python dependencies
COPY requirements.txt $APP_HOME/
RUN pip install --upgrade pip && \
    pip install gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . $APP_HOME/
RUN chmod +x  $APP_HOME/entrypoint.sh


ENTRYPOINT ["sh", "/code/entrypoint.sh"]
