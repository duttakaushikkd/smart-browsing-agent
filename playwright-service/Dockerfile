FROM mcr.microsoft.com/playwright/python:v1.45.0-noble

WORKDIR /app

# Copy configuration and setup files
COPY pyproject.toml README.md ./

# Install python dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY . .

# Expose service port
EXPOSE 8080

# Run FastAPI app
CMD ["python", "main.py"]
