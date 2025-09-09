# Photobooth

A full-screen, touch-friendly photobooth application created for Linux. This app displays a live view from a selected camera, allows you to take photos, and includes several customization options.

## Features

*   **Live Camera View**: Displays a full-screen, real-time feed from your webcam.
*   **Camera Selection**: If you have multiple cameras connected, a dropdown menu allows you to switch between them. On Linux, it will attempt to use `v4l2-ctl` to show descriptive camera names.
*   **Resolution Control**: Choose from a list of supported resolutions for your selected camera to get the best quality picture.
*   **Photo Capture**: A large, round, touch-friendly button lets you snap a photo.
*   **Flash Effect**: A fun, on-screen white flash effect gives you visual feedback when a photo is taken.
*   **Customizable Banner**: Display a custom banner image at the top of the application.
*   **Optional Voice Activation**: Say "Smile!" to start the photo countdown. This is an optional feature.

Before running the application for the first time, you need to generate the necessary image assets. Run the following command:

```bash
python create_assets.py
```

This will create the default banner, birthday frames, and UI icons in the `assets/` directory.

### Voice Activation (Optional)

This application supports voice activation using the "Smile!" command. This is an optional feature. To enable it, you must install the additional dependencies:

```bash
pip install -r requirements-voice.txt
```

If these dependencies are not installed, the application will run without voice activation, and you can continue to use the on-screen button to take photos.

## Configuration

### Banner Image

To replace the default banner at the top of the screen, set the `CUSTOM_BANNER_PATH` environment variable to the absolute path of your desired image file.

For example:
```bash
export CUSTOM_BANNER_PATH="/path/to/your/banner.png"
python main.py
```
If the environment variable is not set, the application will look for a default banner at `assets/default_banner.png`.

## Disclaimer

This application was created as an experiment in vibe coding with Jules.
