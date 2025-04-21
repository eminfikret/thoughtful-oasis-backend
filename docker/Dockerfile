FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy project first
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set permissions for entrypoint
RUN chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]