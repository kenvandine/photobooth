#!/bin/sh
set -e
exec $SNAP/usr/sbin/nginx -c $SNAP/etc/nginx/nginx.conf -g "daemon off;"
