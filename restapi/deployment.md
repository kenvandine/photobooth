# Deployment Guide

This guide explains how to build and deploy the Photo API as a snap package. Snaps are containerized software packages that are simple to create and install.

## Prerequisites

To build the snap, you need to have `snapcraft` installed. You can install it on Ubuntu and other Linux distributions that support snaps with the following command:

```bash
sudo snap install snapcraft --classic
```

## Building the Snap

Navigate to the `restapi` directory where the `snapcraft.yaml` file is located and run the `snapcraft` command:

```bash
cd restapi
snapcraft
```

This will build the snap package in the current directory. The output will be a `.snap` file, for example, `photobooth-api_0.1_amd64.snap`.

## Installing the Snap

Once the snap is built, you can install it using the `snap install` command. Since the snap is not signed by the Snap Store, you need to use the `--dangerous` flag:

```bash
sudo snap install photobooth-api_*.snap --dangerous
```

## Verifying the Installation

After installation, the Gunicorn and Nginx services should start automatically. You can check the status of the services with the following command:

```bash
snap services photobooth-api
```

You should see both the `gunicorn` and `nginx` services running.

## Accessing the API

The Nginx service is configured to listen on port 80. You can now access the Photo API at:

```
http://localhost/api/photos
```

You can test it with `curl`:

```bash
curl http://localhost/api/photos
```

## Uninstalling the Snap

To remove the snap package and all its data, you can use the `snap remove` command:

```bash
sudo snap remove photobooth-api
```

## Enabling SSL (HTTPS)

The snap supports enabling SSL using Let's Encrypt and Certbot. This allows you to serve the API over HTTPS.

### Prerequisites

- You must have a registered domain name that points to the public IP address of the server where the snap is installed.
- The server's firewall must allow traffic on ports 80 and 443.

### Configuration

To enable SSL, you need to set the following snap configuration options:

- `ssl.enabled`: Set to `true` to enable SSL.
- `ssl.domain`: Your fully qualified domain name (e.g., `api.example.com`).
- `ssl.email`: Your email address, for important notifications from Let's Encrypt.

You can set these options using the `snap set` command:

```bash
sudo snap set photobooth-api ssl.enabled=true
sudo snap set photobooth-api ssl.domain="api.example.com"
sudo snap set photobooth-api ssl.email="your-email@example.com"
```

After setting these options, the `nginx` service will automatically try to obtain an SSL certificate from Let's Encrypt. You can check the status of the service and the logs for any issues:

```bash
snap services photobooth-api
sudo snap logs photobooth-api.nginx
```

If successful, the API will be available at `https://api.example.com`. The snap will also automatically handle the renewal of the certificate.
