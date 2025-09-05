# Photobooth

A full-screen, touch-friendly photobooth application created for Linux. This app displays a live view from a selected camera, allows you to take photos, and includes several customization options.

## Features

*   **Live Camera View**: Displays a full-screen, real-time feed from your webcam.
*   **Camera Selection**: If you have multiple cameras connected, a dropdown menu allows you to switch between them. On Linux, it will attempt to use `v4l2-ctl` to show descriptive camera names.
*   **Resolution Control**: Choose from a list of supported resolutions for your selected camera to get the best quality picture.
*   **Photo Capture**: A large, round, touch-friendly button lets you snap a photo.
*   **Flash Effect**: A fun, on-screen white flash effect gives you visual feedback when a photo is taken.
*   **Customizable Banner**: Display a custom banner image at the top of the application.

## Configuration

### Banner Image

To replace the default banner at the top of the screen, set the `CUSTOM_BANNER_PATH` environment variable to the absolute path of your desired image file.

For example:
```bash
export CUSTOM_BANNER_PATH="/path/to/your/banner.png"
python main.py
```
If the environment variable is not set, the application will look for a default banner at `assets/default_banner.png`. If this file does not exist, a plain grey banner will be created automatically.

## Disclaimer

This application was created as an experiment in vibe coding with Jules.
