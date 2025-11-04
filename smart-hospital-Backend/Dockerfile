# Use a specific, stable version of Python for reproducible builds.
# The 'slim' variant is used to minimize the final image size.
FROM python:3.10-slim

# Set the working directory within the container. All subsequent commands
# will be run from this path.
WORKDIR /app

# Copy only the requirements file first to leverage Docker's layer caching.
# This step is only re-run if the requirements.txt file changes.
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt.
# --no-cache-dir: Disables the pip cache to keep the image size smaller.
# --upgrade pip: Ensures the latest version of pip is used for installation.
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copy the rest of the application source code into the container's working directory.
# This is done *after* installing dependencies to avoid re-installing them on every code change.
COPY . .

# Expose port 5000, which is the port the Flask application will listen on.
EXPOSE 5000

# Define the command to run the application when the container starts.
# This runs the Flask development server. For production, a Gunicorn server would be used.
CMD ["python", "main.py"]