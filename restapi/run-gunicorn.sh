#!/bin/sh
set -e
cd $SNAP
exec $SNAP/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 api:app
