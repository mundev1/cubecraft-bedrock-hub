FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure start script has executable permissions
RUN chmod +x start.sh

# Environment and port defaults
ENV PORT=5055
ENV PYTHONUNBUFFERED=1
EXPOSE 5055

# Run the unified starter
CMD ["bash", "start.sh"]
