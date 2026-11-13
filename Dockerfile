FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up user with UID 1000 (standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set ownership and executable permissions
RUN chown -R user:user /app && chmod +x start.sh

# Run as non-root user
USER user

# Default port for Hugging Face Spaces is 7860
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
EXPOSE 7860

# Run the unified starter
CMD ["bash", "start.sh"]
