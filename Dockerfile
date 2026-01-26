# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (Render usually sets PORT env var)
EXPOSE 5001

# Command to run the application
# Using python app.py directly since it uses threading and specific loops, 
# but for production gunicorn is usually better. 
# However, given the app structure (threading, globals), app.py might be safer to run directly for now.
# We will use CMD to run it directly to preserve the threading behavior designed in app.py.
CMD ["python", "app.py"]
