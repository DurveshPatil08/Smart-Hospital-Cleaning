# Phase 2: Dockerfile for the Frontend

# 1. Use an official, lightweight Nginx web server image.
# 'alpine' images are very small and secure.
FROM nginx:stable-alpine

# 2. Copy all the frontend files into the default Nginx web root directory.
# Nginx will automatically serve the index.html file from here.
COPY . /usr/share/nginx/html

# That's it! The base Nginx image already has a command to start the server,
# and it's configured to expose port 80 by default.

