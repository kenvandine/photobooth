#!/bin/bash

# Set the custom banner path if it's not already set
_banner=$(snapctl get banner)
if [ -f "$_banner" ]; then
    export CUSTOM_BANNER_PATH="$_banner"
fi

# Run the main application
$SNAP/gnome-platform/usr/bin/python3.12 $SNAP/main.py
