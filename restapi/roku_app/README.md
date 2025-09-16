# Roku Photo Slideshow App

This Roku application displays a photo slideshow from the Photobooth API. It replicates the functionality of the ReactJS web frontend.

## **IMPORTANT: Configuration**

Before you can use this app, you **MUST** configure the API server address.

1.  Open the file: `components/MainScene.brs`
2.  Find the following line (around line 13):
    ```brightscript
    m.apiUrl = "http://<YOUR_IP_ADDRESS>:5000/api"
    ```
3.  Replace `<YOUR_IP_ADDRESS>` with the actual IP address of the computer running the Photobooth API server. For example:
    ```brightscript
    m.apiUrl = "http://192.168.1.100:5000/api"
    ```

## How to Deploy to a Roku Device

To run this application on your Roku device, you need to enable developer mode and "sideload" the application package.

### 1. Enable Developer Mode on Your Roku

-   Using your Roku remote, press the following sequence:
    **Home, Home, Home, Up, Up, Right, Left, Right, Left, Right**
-   A "Developer Settings" screen will appear. Follow the on-screen instructions to enable developer mode and accept the license agreement.
-   Your Roku will restart, and you will be shown a URL (e.g., `http://192.168.1.X`). This is the URL of your Roku's developer web interface. Note it down.

### 2. Package the Application

-   You need to create a `.zip` file containing all the files and folders inside this `roku_app` directory (`source`, `components`, `images`, `manifest`, and this `README.md`).
-   Make sure the `manifest` file is at the root of the zip archive, not inside a `roku_app` subfolder.
-   On Linux or macOS, you can navigate into the `roku_app` directory and run:
    ```bash
    zip -r ../photobooth_roku.zip .
    ```

### 3. Install the Application

-   Open a web browser on your computer and navigate to the URL of your Roku device that you noted in Step 1.
-   You will see the "Development Application Installer" page.
-   Click the "Upload" button and select the `photobooth_roku.zip` file you just created.
-   Click "Install". The application should now be installed on your Roku and will launch automatically.

## Controls

-   **Left/Right Arrows**: Navigate to the previous/next photo.
-   **OK / Play / Pause**: Toggle the slideshow between playing and paused.
