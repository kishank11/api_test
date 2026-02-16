# Use a slim Python image
FROM python:3.11-slim

# Install system dependencies for OCR and Docling
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the code
COPY . .

# Match the port AWS App Runner expects
EXPOSE 8080

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "application:application"]
