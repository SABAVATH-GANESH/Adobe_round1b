FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port if you run a web app (like Flask)
EXPOSE 5000

# Default command to run your main script
CMD ["python", "main.py"]