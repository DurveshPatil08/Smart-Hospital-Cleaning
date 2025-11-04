# Use a specific, stable version of Nginx based on the lightweight Alpine Linux.
# 'alpine' images are minimal, which improves security and reduces image size.
FROM nginx:stable-alpine

# Copy the entire contents of the frontend directory (HTML, CSS, JS, etc.)
# into the default Nginx web root directory.
COPY . /usr/share/nginx/html

# The base Nginx image already includes a default configuration to serve files
# from /usr/share/nginx/html on port 80. No further configuration is needed.

# Expose port 80 for the Nginx web server.
EXPOSE 80

# The base image's default CMD starts the Nginx server in the foreground.