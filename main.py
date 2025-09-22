"""
A Kivy-based camera application for capturing photos.

This application provides a simple interface to select from available cameras,
choose a resolution, and capture images. It features custom-drawn buttons
and a flash effect upon capturing a photo. Captured photos are saved to a
'photos' directory with a timestamped filename.

The application can be customized with a banner by setting the
`CUSTOM_BANNER_PATH` environment variable. If not set, a default banner is
created and used.
"""
import os
os.environ['KIVY_NO_ARGS'] = '1'
import kivy
kivy.require('2.3.1')

from kivy.app import App
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, Rectangle, StencilPush, StencilPop
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import os
import random
import glob
from datetime import datetime
import logging
import subprocess
import re
import requests
import argparse
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None
VOICE_ENABLED = os.environ.get('VOICE_ENABLED')
if VOICE_ENABLED:
    from voice_listener import VoiceListener
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
DEFAULT_BANNER_PATH = 'assets/default_banner.png'
PHOTOBOOTH_URL = os.environ.get('PHOTOBOOTH_URL')
RESOLUTION = os.environ.get('RESOLUTION')
# --- END CONFIGURATION ---

def is_raspberry_pi():
    """Checks if the system is a Raspberry Pi."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            if 'raspberry pi' in f.read().lower():
                return True
    except Exception:
        pass
    return False

class PiCamera2Wrapper:
    def __init__(self, camera_num=0, resolution=(640, 480)):
        if Picamera2 is None:
            msg = "picamera2 library not found or failed to import. " \
                  "Please ensure it is installed in the correct Python environment " \
                  "and that all its system dependencies are met."
            raise ImportError(msg)
        self.picam2 = Picamera2(camera_num=camera_num)
        config = self.picam2.create_preview_configuration(main={"format": "RGB888", "size": resolution})
        self.picam2.configure(config)
        self.picam2.start()
        self._is_opened = True

    def isOpened(self):
        return self._is_opened

    def read(self):
        if not self._is_opened:
            return False, None
        # capture_array returns a numpy array in RGB format.
        frame = self.picam2.capture_array()
        return True, frame

    def release(self):
        if self._is_opened:
            self.picam2.stop()
            self._is_opened = False

    def set(self, prop, value):
        # This is a dummy implementation for now.
        # The picamera2 library uses a different method for setting controls.
        logging.info(f"PiCamera2Wrapper: set property {prop} to {value} (not implemented)")
        return True

    def get(self, prop):
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return self.picam2.camera_config['main']['size'][0]
        if prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.picam2.camera_config['main']['size'][1]
        return 0

# A list of common resolutions to test
STANDARD_RESOLUTIONS = [
    (640, 480),
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1920, 1080),
    (2592, 1944),
    (3840, 2160)
]

class RoundButton(ButtonBehavior, Widget):
    """
    A circular button with a visual feedback effect on press.

    This widget combines `ButtonBehavior` with a custom-drawn circle and ring
    to create a round button. It shows a darkening effect when pressed.
    """
    def __init__(self, **kwargs):
        """Initializes the RoundButton widget."""
        super(RoundButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        with self.canvas.before:
            Color(0.4, 0.4, 0.4, 1)  # Dark grey for the outer ring
            self.ring = Ellipse()
            Color(0.7, 0.7, 0.7, 1)  # Lighter grey for the inner circle
            self.circle = Ellipse()
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.update_graphics()

    def update_graphics(self, *args):
        """
        Updates the position and size of the circle and ring graphics.

        This method is called when the button's position or size changes.
        """
        self.ring.pos = self.pos
        self.ring.size = self.size
        inner_size = self.width * 0.8
        inner_pos_x = self.x + (self.width - inner_size) / 2
        inner_pos_y = self.y + (self.height - inner_size) / 2
        self.circle.pos = (inner_pos_x, inner_pos_y)
        self.circle.size = (inner_size, inner_size)

    def on_state(self, widget, value):
        """
        Handles the button's state change (e.g., pressed, released).

        A visual feedback (a dark overlay) is added when the button is
        in the 'down' state and removed otherwise.

        Args:
            widget: The widget instance that triggered the event.
            value: The new state of the button.
        """
        if value == 'down':
            with self.canvas.after:
                Color(0, 0, 0, 0.2)
                self.feedback = Ellipse(pos=self.pos, size=self.size)
        else:
            if hasattr(self, 'feedback'):
                self.canvas.after.remove(self.feedback)


class RoundImageButton(ButtonBehavior, Image):
    """
    A circular button that displays an image, clipped to a circular shape.

    This widget uses a stencil to mask the image into a circle, creating a
    round image button. It inherits from `ButtonBehavior` to provide button-like
    functionality.
    """
    def __init__(self, **kwargs):
        """Initializes the RoundImageButton widget."""
        super(RoundImageButton, self).__init__(**kwargs)
        with self.canvas.before:
            self.stencil = StencilPush()
            self.stencil_shape = Ellipse()
        with self.canvas.after:
            self.stencil_pop = StencilPop()

        self.bind(pos=self.update_stencil, size=self.update_stencil)

    def update_stencil(self, *args):
        """
        Updates the position and size of the stencil shape.

        This ensures the circular mask is always aligned with the button's
        position and size.
        """
        self.stencil_shape.pos = self.pos
        self.stencil_shape.size = self.size


class CameraApp(App):
    """
    The main application class for the camera app.

    This class orchestrates the user interface, camera hardware interaction,
    and photo capture logic. It builds the GUI using Kivy widgets and manages
    camera selection, resolution changes, and the capture process.
    """
    def __init__(self, device=None, resolution=None, **kwargs):
        super(CameraApp, self).__init__(**kwargs)
        self.device = device
        self.resolution = resolution
        self.camera_type = 'default'

    def get_available_cameras(self):
        """
        Detects and lists available video cameras on the system, determining the
        best backend for each camera.
        """
        cameras = {}
        if not is_raspberry_pi():
            # Fallback for non-Pi systems
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras[f"Camera {i}"] = {'index': i, 'type': 'default'}
                    cap.release()
            logging.info(f"Available cameras (non-Pi): {cameras}")
            return cameras

        # Raspberry Pi specific detection
        try:
            output = subprocess.check_output(['v4l2-ctl', '--list-devices'], text=True)
            current_camera_name = ""
            for line in output.splitlines():
                if not line.startswith('\t'):
                    current_camera_name = line.strip().split(' (')[0]
                elif '/dev/video' in line:
                    camera_type = None
                    if 'unicam' in current_camera_name.lower():
                        camera_type = 'picamera'
                    elif 'usb' in current_camera_name.lower():
                        camera_type = 'v4l2'

                    if camera_type:
                        match = re.search(r'/dev/video(\d+)', line)
                        if match:
                            index = int(match.group(1))
                            # Use the device name and index to create a unique key
                            unique_key = f"{current_camera_name} ({index})"
                            if unique_key not in cameras:
                                if camera_type == 'picamera' and Picamera2 is None:
                                    logging.warning("PiCamera detected, but picamera2 library is not installed.")
                                    continue
                                cameras[unique_key] = {'index': index, 'type': camera_type}
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("v4l2-ctl not found or failed. Cannot perform Pi-specific camera detection.")

        # Fallback if v4l2-ctl fails or finds no specific cameras
        if not cameras:
            logging.warning("No specific Pi cameras found, falling back to default enumeration.")
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras[f"Camera {i}"] = {'index': i, 'type': 'default'}
                    cap.release()

        logging.info(f"Available cameras: {cameras}")
        return cameras

    def get_supported_resolutions(self, camera_index, camera_type='default'):
        """
        Determines the supported resolutions for a given camera.

        It checks a predefined list of common resolutions against the camera's
        capabilities.

        Args:
            camera_index (int): The index of the camera to check.
            camera_type (str): The type of camera ('picamera', 'v4l2', 'default').

        Returns:
            list: A list of strings, where each string represents a
                  supported resolution (e.g., "1920x1080").
        """
        if camera_type == 'picamera':
            # For PiCamera2, we assume it supports all standard resolutions.
            # A more advanced implementation could query sensor modes.
            return [f"{w}x{h}" for w, h in STANDARD_RESOLUTIONS]

        supported_resolutions = []
        backend = cv2.CAP_V4L2 if camera_type == 'v4l2' else cv2.CAP_ANY
        cap = cv2.VideoCapture(camera_index, backend)
        if not cap.isOpened():
            logging.error(f"Could not open camera index {camera_index} to get resolutions.")
            return []
        # Test a list of standard resolutions
        for w, h in STANDARD_RESOLUTIONS:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # If the camera accepts the resolution, add it to the list
            if actual_w == w and actual_h == h:
                supported_resolutions.append(f"{w}x{h}")
        cap.release()
        logging.info(f"Supported resolutions for camera {camera_index}: {supported_resolutions}")
        return supported_resolutions

    def build(self):
        """
        Builds the application's user interface.

        This method sets up the layout, widgets, and camera feed. It's the
        main entry point for creating the app's visual components.

        Returns:
            FloatLayout: The root widget of the application.
        """
        Window.fullscreen = True
        self.birthday_frame = None
        self.frame_files = sorted(glob.glob('assets/frames/*.png'))
        self.current_frame_index = 0
        if self.frame_files:
            # Start with a random frame
            self.current_frame_index = random.randint(0, len(self.frame_files) - 1)
            frame_path = self.frame_files[self.current_frame_index]
            self.birthday_frame = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            logging.info(f"Loaded birthday frame: {frame_path}")

        Window.clearcolor = (0.678, 0.847, 0.902, 1)  # Light blue background
        root = FloatLayout()
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Add a banner at the top, custom or default
        banner_path = os.environ.get('CUSTOM_BANNER_PATH', DEFAULT_BANNER_PATH)
        if os.path.exists(banner_path):
            banner = Image(
                source=banner_path,
                size_hint_y=None,
                height=100,
                allow_stretch=True,
                keep_ratio=False
            )
            main_layout.add_widget(banner)
        else:
            logging.warning(f"Banner image not found at path: {banner_path}")

        # This widget will display the camera feed
        self.camera_view = Image()
        main_layout.add_widget(self.camera_view)

        # Always get the full list of cameras with their types
        all_cameras = self.get_available_cameras()

        if self.device is not None:
            # If a device is specified, find it in the list of all cameras
            self.available_cameras = {}
            for name, info in all_cameras.items():
                if info['index'] == self.device:
                    self.available_cameras[name] = info
                    break
            if not self.available_cameras:
                # If the specified device was not found, fallback to using it directly
                logging.warning(f"Device {self.device} not found in v4l2-ctl list. Falling back to direct use.")
                # When a device is specified on a Pi, assume it's the Pi Camera.
                camera_type = 'picamera' if is_raspberry_pi() else 'default'
                self.available_cameras = {f"Device: {self.device}": {'index': self.device, 'type': camera_type}}
        else:
            self.available_cameras = all_cameras

        if not self.available_cameras:
            logging.error("No cameras found!")
            # Optionally, display a message to the user in the UI
            return root

        camera_names = list(self.available_cameras.keys())

        # Spinner for resolution selection (will be moved to a popup)
        self.resolution_selector = Spinner(text="Resolution", values=[], size_hint_y=None, height=50)
        self.resolution_selector.bind(text=self.on_resolution_select)

        # Layout for the capture button, centered horizontally
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        button_layout.add_widget(Widget())  # Left spacer
        self.capture_button = RoundButton(size_hint=(None, None), size=(80, 80))
        self.capture_button.bind(on_press=self.capture_photo)
        button_layout.add_widget(self.capture_button)
        button_layout.add_widget(Widget())  # Right spacer
        main_layout.add_widget(button_layout)

        # The FloatLayout is used to allow overlaying widgets
        root.add_widget(main_layout)

        # A button to open camera and resolution settings
        self.camera_switch_button = RoundImageButton(
            source='assets/system-settings.png',
            size_hint=(None, None),
            size=(32, 32),
            pos_hint={'x': 0.05, 'y': 0.05}
        )
        self.camera_switch_button.bind(on_press=self.open_camera_selector)
        root.add_widget(self.camera_switch_button)

        # A button to change the birthday frame
        self.frame_switch_button = RoundImageButton(
            source='assets/change-frame.png',
            size_hint=(None, None),
            size=(32, 32),
            pos_hint={'right': 0.95, 'y': 0.05}
        )
        self.frame_switch_button.bind(on_press=self.change_birthday_frame)
        root.add_widget(self.frame_switch_button)

        # Add a label for the countdown timer
        self.countdown_label = Label(
            text="",
            font_size='200sp',
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=5,
            outline_color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root.add_widget(self.countdown_label)
        self.countdown_active = False

        # A white widget for the flash effect
        self.flash = Widget(opacity=0)
        with self.flash.canvas:
            Color(1, 1, 1)
            self.flash_rect = Rectangle(size=self.flash.size, pos=self.flash.pos)
        self.flash.bind(size=self._update_flash_rect, pos=self._update_flash_rect)
        root.add_widget(self.flash)

        # Initialize with the first available camera
        first_camera_name = camera_names[0]
        self.update_camera(first_camera_name)

        # Schedule the camera feed update
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS

        # Create a Kivy-safe trigger for capturing a photo
        self.capture_trigger = Clock.create_trigger(self.capture_photo)
        # Initialize and start the voice listener
        try:
            self.voice_listener = VoiceListener(callback=self.capture_trigger)
            self.voice_listener.start()
        except Exception as e:
            logging.error(f"Failed to start voice listener: {e}")
            self.voice_listener = None

        return root

    def _update_flash_rect(self, instance, value):
        """
        Callback to update the flash rectangle's size and position.

        Args:
            instance: The widget instance.
            value: The new size or position value.
        """
        self.flash_rect.pos = instance.pos
        self.flash_rect.size = instance.size

    def update_camera(self, camera_name):
        """
        Switches the active camera and updates the resolution list.

        Args:
            camera_name (str): The name of the camera to switch to.
        """
        camera_info = self.available_cameras[camera_name]
        selected_index = camera_info['index']
        camera_type = camera_info['type']
        self.camera_type = camera_type
        logging.info(f"Switching to camera: {camera_name} (index: {selected_index}, type: {camera_type})")

        # Release the previous camera capture if it exists
        if hasattr(self, 'capture') and self.capture:
            self.capture.release()

        # Update resolutions and set the camera to the highest available one
        resolutions = self.get_supported_resolutions(selected_index, camera_type)
        self.resolution_selector.values = resolutions

        w, h = (1920, 1080) # Default resolution
        if resolutions:
            if not self.resolution or self.resolution not in resolutions:
                self.resolution = resolutions[-1] # Default to highest
            self.resolution_selector.text = self.resolution
            w, h = map(int, self.resolution.split('x'))

        if camera_type == 'picamera':
            self.capture = PiCamera2Wrapper(camera_num=selected_index, resolution=(w, h))
        else:
            backend = cv2.CAP_V4L2 if camera_type == 'v4l2' else cv2.CAP_ANY
            self.capture = cv2.VideoCapture(selected_index, backend)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        logging.info(f"Set camera {selected_index} to {w}x{h} with type {camera_type}")

    def on_camera_select(self, camera_name):
        """
        Event handler for camera selection.

        Args:
            camera_name (str): The name of the selected camera.
        """
        self.update_camera(camera_name)

    def open_camera_selector(self, instance):
        """
        Opens a popup for selecting the camera and resolution.

        Args:
            instance: The widget instance that triggered the event.
        """
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup = Popup(title='Camera & Resolution', content=content, size_hint=(0.8, 0.9))

        # Add camera selection buttons
        content.add_widget(Label(text='Cameras', size_hint_y=None, height=40))
        for camera_name in self.available_cameras.keys():
            btn = Button(text=camera_name, size_hint_y=None, height=50)
            btn.bind(on_release=lambda x, name=camera_name: self.select_camera_and_close(name, popup))
            content.add_widget(btn)

        # Add the resolution spinner to the popup
        content.add_widget(Label(text='Resolution', size_hint_y=None, height=40))
        if self.resolution_selector.parent:
            # Ensure the widget is not attached to another parent
            self.resolution_selector.parent.remove_widget(self.resolution_selector)
        content.add_widget(self.resolution_selector)

        def cleanup_on_dismiss(popup_instance):
            """
            Ensures the resolution selector is removed from the popup content
            when the popup is dismissed, so it can be re-added later without issues.
            """
            if self.resolution_selector.parent:
                self.resolution_selector.parent.remove_widget(self.resolution_selector)
        popup.bind(on_dismiss=cleanup_on_dismiss)

        # Add a close button to the popup
        close_button = Button(text='Close', size_hint_y=None, height=50)
        close_button.bind(on_release=popup.dismiss)
        content.add_widget(close_button)

        popup.open()

    def select_camera_and_close(self, camera_name, popup):
        """
        Selects a camera and closes the popup.

        Args:
            camera_name (str): The name of the camera to select.
            popup (Popup): The popup instance to be closed.
        """
        self.on_camera_select(camera_name)
        popup.dismiss()

    def change_birthday_frame(self, *args):
        """
        Cycles to the next available birthday frame.
        """
        if not self.frame_files:
            return

        # Increment index and wrap around
        self.current_frame_index = (self.current_frame_index + 1) % len(self.frame_files)

        # Load the new frame
        frame_path = self.frame_files[self.current_frame_index]
        self.birthday_frame = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
        logging.info(f"Changed birthday frame to: {frame_path}")

    def on_resolution_select(self, spinner, text):
        """
        Event handler for resolution selection from the spinner.

        Args:
            spinner: The spinner instance.
            text (str): The selected resolution string (e.g., "1920x1080").
        """
        if text == 'Default' or not hasattr(self, 'capture') or not self.capture.isOpened():
            return
        w, h = map(int, text.split('x'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        logging.info(f"Resolution changed to {w}x{h}")

    def _apply_overlay(self, frame):
        """
        Applies the birthday frame overlay to a given frame.
        """
        if self.birthday_frame is None:
            return frame

        # Resize frame overlay to match camera frame size
        h, w, _ = frame.shape
        overlay_resized = cv2.resize(self.birthday_frame, (w, h))

        # Separate the overlay into color and alpha channels
        overlay_rgb = overlay_resized[:, :, :3]
        alpha = overlay_resized[:, :, 3] / 255.0

        # Blend the overlay with the frame
        blended_frame = (1 - alpha)[:, :, None] * frame + alpha[:, :, None] * overlay_rgb
        return blended_frame.astype('uint8')

    def update(self, dt):
        """
        Updates the camera view with a new frame.

        This method is called repeatedly by the Kivy Clock.

        Args:
            dt (float): The time elapsed since the last update.
        """
        if not hasattr(self, 'capture') or not self.capture.isOpened():
            return
        ret, frame = self.capture.read()
        if ret:
            # Frame is now always BGR. Apply the overlay.
            frame = self._apply_overlay(frame)

            # Convert the final BGR frame to RGB for Kivy texture
            if self.camera_type == 'picamera':
                # Frame is already RGB
                frame_rgb = frame
            else:
                # Frame is BGR, convert to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Flip the frame vertically (otherwise it's upside down)
            buf1 = cv2.flip(frame_rgb, 0)
            # Convert the frame to a 1D byte buffer
            buf = buf1.tobytes()
            # Create a Kivy texture from the byte buffer
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='rgb'
            )
            image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            # Display the texture in the Image widget
            self.camera_view.texture = image_texture

    def do_flash(self):
        """Triggers a flash animation on the screen."""
        self.flash.opacity = 1
        Animation(opacity=0, duration=0.2).start(self.flash)

    def capture_photo(self, *args):
        """
        Starts a countdown before taking a photo.
        """
        if self.countdown_active:
            return

        self.countdown_active = True
        self.capture_button.disabled = True
        self.countdown_number = 3
        self.countdown_label.text = str(self.countdown_number)
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        """
        Updates the countdown label and takes a photo when the countdown finishes.
        """
        self.countdown_number -= 1
        if self.countdown_number > 0:
            self.countdown_label.text = str(self.countdown_number)
        else:
            self.countdown_label.text = ""
            self._take_and_save_photo()
            self.countdown_active = False
            self.capture_button.disabled = False
            return False  # Stop the clock event

    def _take_and_save_photo(self, *args):
        """
        Captures a photo, saves it, and uploads it to the backend.
        """
        if not hasattr(self, 'capture') or not self.capture.isOpened():
            logging.error("No camera is active to take a photo.")
            return
        # Create the 'photos' directory if it doesn't exist
        if not os.path.exists("photos"):
            os.makedirs("photos")
        ret, frame = self.capture.read()
        if ret:
            # Frame is BGR, overlay is BGRA. This is what _apply_overlay expects.
            frame_with_overlay = self._apply_overlay(frame)

            # If the camera is a picamera, the frame is RGB, but imwrite expects BGR.
            if self.camera_type == 'picamera':
                frame_to_save = cv2.cvtColor(frame_with_overlay, cv2.COLOR_RGB2BGR)
            else:
                frame_to_save = frame_with_overlay

            now = datetime.now()
            filename = f"photos/photo_{now.strftime('%Y%m%d_%H%M%S')}.png"
            # cv2.imwrite expects BGR, which is what we have.
            cv2.imwrite(filename, frame_to_save)
            logging.info(f"Photo saved as {filename}")
            self.do_flash()

            # Upload the photo to the backend if URL is set
            if PHOTOBOOTH_URL:
                logging.info("Uploading photo to server")
                self._upload_photo(filename)

    def _upload_photo(self, filename):
        """
        Uploads the photo to the backend API.
        """
        try:
            with open(filename, 'rb') as f:
                files = {'file': (os.path.basename(filename), f, 'image/png')}
                response = requests.post(PHOTOBOOTH_URL, files=files)
                if response.status_code == 201:
                    logging.info(f"Photo uploaded successfully: {response.json()}")
                else:
                    logging.error(f"Failed to upload photo: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error uploading photo: {e}")

    def on_stop(self):
        """
        Cleanly releases the camera capture and stops the voice listener
        when the application is closed.
        """
        if hasattr(self, 'voice_listener') and self.voice_listener:
            self.voice_listener.stop()
        if hasattr(self, 'capture') and self.capture:
            self.capture.release()
            logging.info("Camera released.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A Kivy-based camera app.")
    parser.add_argument('--device', help='The v4l device to use (e.g., /dev/video0)')
    args = parser.parse_args()
    device = args.device
    if device:
        # Try to extract a numeric index from the end of the string,
        # as cv2.VideoCapture prefers integer indices.
        match = re.search(r'\d+$', device)
        if match:
            device = int(match.group(0))
    CameraApp(device=device, resolution=RESOLUTION).run()
