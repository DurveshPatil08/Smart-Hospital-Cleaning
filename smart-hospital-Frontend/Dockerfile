# 1. Use the stable-alpine Nginx image
FROM nginx:stable-alpine

# 2. Copy your static files (HTML, CSS, JS)
COPY . /usr/share/nginx/html

# 3. Expose port 80 (for documentation, Render uses $PORT)
EXPOSE 80

# 4. This command will find the default Nginx config,
#    replace 'listen 80;' with 'listen $PORT;',
#    and then start the Nginx server.
CMD sh -c "sed -i 's/listen 80;/listen $PORT;/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
