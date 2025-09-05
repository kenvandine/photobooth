#!/bin/bash

# Set the custom banner path if it's not already set
if [ -z "$CUSTOM_BANNER_PATH" ]; then
    export CUSTOM_BANNER_PATH="$SNAP/assets/default_banner.png"
fi

# Run the main application
$SNAP/usr/bin/python3 $SNAP/main.py
