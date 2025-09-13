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
