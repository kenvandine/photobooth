#!/bin/sh
set -e

# Create writable nginx config and lib directories
mkdir -p $SNAP_COMMON/etc/nginx/sites-available
mkdir -p $SNAP_COMMON/etc/nginx/sites-enabled
mkdir -p $SNAP_COMMON/var/lib/nginx

# Copy the main nginx.conf and update paths to use the writable sites-enabled directory
cp $SNAP/etc/nginx/nginx.conf $SNAP_COMMON/etc/nginx/nginx.conf
sed -i -e "s|/etc/nginx/sites-enabled/|/var/snap/photobooth-api/common/etc/nginx/sites-enabled/|g" $SNAP_COMMON/etc/nginx/nginx.conf

# Copy the site-specific config to the writable location
cp $SNAP/etc/nginx/sites-available/photobooth-api $SNAP_COMMON/etc/nginx/sites-available/photobooth-api

# Copy mime.types
cp $SNAP/etc/nginx/mime.types $SNAP_COMMON/etc/nginx/mime.types

# Create the symlink to the site-specific config in the writable location
ln -sf ../sites-available/photobooth-api $SNAP_COMMON/etc/nginx/sites-enabled/photobooth-api

# Run the certbot script to handle SSL configuration.
# This script will modify the nginx config in $SNAP_COMMON if SSL is enabled.
$SNAP/bin/run-certbot.sh

# Start nginx using the (potentially modified) configuration in $SNAP_COMMON
exec $SNAP/usr/sbin/nginx -c $SNAP_COMMON/etc/nginx/nginx.conf -g "daemon off;"
