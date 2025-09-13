#!/bin/sh
set -e
exec /usr/sbin/nginx -c $SNAP/etc/nginx/nginx.conf -g "daemon off;"
