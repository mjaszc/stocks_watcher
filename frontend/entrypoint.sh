#!/bin/bash
set -e

envsubst '$$NGINX_SERVER_NAME' < /etc/nginx/conf.d/default.conf > /tmp/default.conf

mv /tmp/default.conf /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
