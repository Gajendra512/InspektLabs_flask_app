# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables to avoid Python buffering
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install the necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8010 for Flask and 3306 for MySQL
EXPOSE 8010 
# Start MySQL service and Flask app (running in the background)
CMD flask run --host=0.0.0.0 --port=8010
