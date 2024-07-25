# syntax=docker/dockerfile:1.3
FROM --platform=linux/amd64 python:3.12.2

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Set the PORT environment variable
ENV PORT 8080

# Expose port 8080 to the outside world
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "main.py"]