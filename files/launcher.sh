#!/bin/bash

# Set the custom banner path if it's not already set
_banner=$(snapctl get banner)
if [ -f "$_banner" ]; then
    export CUSTOM_BANNER_PATH="$_banner"
fi

_voice=$(snapctl get voice)
if [[ "$_voice" == "true" ]]; then
    export VOICE_ENABLED=1
fi

export DEVICE_ARGS=""

_device=$(snapctl get device)
echo $_device
if [[ -n "$_device" ]]; then
    export DEVICE_ARGS="--device $_device"
fi

# Run the main application
$SNAP/gnome-platform/usr/bin/python3.12 $SNAP/main.py $DEVICE_ARGS $@
