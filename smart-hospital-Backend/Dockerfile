# Phase 1: Dockerfile for the Backend

# 1. Start with an official Python base image.
# Using a 'slim' version keeps the final image size smaller.
FROM python:3.10-slim

# 2. Set the working directory inside the container.
# This is where our application code will live.
WORKDIR /app

# 3. Copy only the requirements file first to leverage Docker's caching.
# This layer will only be re-built if requirements.txt changes.
COPY requirements.txt .

# 4. Install the Python dependencies.
# --no-cache-dir ensures we don't store the pip cache, making the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application source code into the container.
COPY . .

# 6. Expose the port that the Flask application runs on.
EXPOSE 5000

# 7. Define the command to run the application when the container starts.
CMD ["python", "main.py"]

