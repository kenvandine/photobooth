#!/bin/sh
set -e

# Get snap settings
SSL_ENABLED=$(snapctl get ssl.enabled || echo "false")
DOMAIN=$(snapctl get ssl.domain || echo "")
EMAIL=$(snapctl get ssl.email || echo "")

if [ "$SSL_ENABLED" = "true" ]; then
  if [ -z "$DOMAIN" ]; then
    echo "SSL is enabled, but 'ssl.domain' is not set. Please set it using 'snap set photobooth-api ssl.domain=<your-domain>'."
    exit 1
  fi

  if [ -z "$EMAIL" ]; then
    echo "SSL is enabled, but 'ssl.email' is not set. Please set it using 'snap set photobooth-api ssl.email=<your-email>'."
    exit 1
  fi

  # Check if a certificate already exists for the domain
  if [ ! -f "$SNAP_COMMON/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "Certificate for $DOMAIN not found. Obtaining a new one..."
    # Use certbot with the nginx plugin to obtain a certificate.
    # The --nginx-server-root tells certbot where to find the nginx configuration.
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --config-dir "$SNAP_COMMON/etc/letsencrypt" --work-dir "$SNAP_COMMON/var/lib/letsencrypt" --logs-dir "$SNAP_COMMON/var/log/letsencrypt" --nginx-server-root "$SNAP_COMMON/etc/nginx"
  else
    echo "Certificate for $DOMAIN found. Checking for renewal..."
    # The 'renew' command will check the certificate's expiration and renew if it's close.
    certbot renew --config-dir "$SNAP_COMMON/etc/letsencrypt" --work-dir "$SNAP_COMMON/var/lib/letsencrypt" --logs-dir "$SNAP_COMMON/var/log/letsencrypt"
  fi
fi

exit 0
