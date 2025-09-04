import kivy
kivy.require('2.3.1')

from kivy.app import App
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import os
from datetime import datetime
import logging
import subprocess
import re

logging.basicConfig(level=logging.INFO)

# A list of common resolutions to test
STANDARD_RESOLUTIONS = [
    (640, 480),
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1920, 1080),
    (3840, 2160)
]

class RoundButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super(RoundButton, self).__init__(**kwargs)
        self.background_normal = '' # Remove default button background
        self.background_down = ''
        with self.canvas.before:
            # Outer ring (a bit darker)
            Color(0.4, 0.4, 0.4, 1)
            self.ring = Ellipse()
            # Inner circle (the main button body)
            Color(0.7, 0.7, 0.7, 1)
            self.circle = Ellipse()

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.update_graphics()

    def update_graphics(self, *args):
        self.ring.pos = self.pos
        self.ring.size = self.size
        # Center the inner circle, make it 80% of the size
        inner_size = self.width * 0.8
        inner_pos_x = self.x + (self.width - inner_size) / 2
        inner_pos_y = self.y + (self.height - inner_size) / 2
        self.circle.pos = (inner_pos_x, inner_pos_y)
        self.circle.size = (inner_size, inner_size)

    def on_state(self, widget, value):
        # Change color on press
        if value == 'down':
            with self.canvas.after:
                Color(0, 0, 0, 0.2)
                self.feedback = Ellipse(pos=self.pos, size=self.size)
        else: # value == 'normal'
            if hasattr(self, 'feedback'):
                self.canvas.after.remove(self.feedback)

class CameraApp(App):

    def get_available_cameras(self):
        """Detects available cameras and their descriptive names."""
        cameras = {}
        try:
            output = subprocess.check_output(['v4l2-ctl', '--list-devices'], text=True)
            current_camera_name = ""
            for line in output.splitlines():
                if not line.startswith('\t'):
                    current_camera_name = line.strip().split(' (')[0]
                elif '/dev/video' in line:
                    match = re.search(r'/dev/video(\d+)', line)
                    if match:
                        index = int(match.group(1))
                        cap = cv2.VideoCapture(index)
                        if cap.isOpened():
                            cameras[current_camera_name] = index
                            cap.release()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.warning("v4l2-ctl not found or failed. Falling back to index-based detection.")
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras[f"Camera {i}"] = i
                    cap.release()

        logging.info(f"Available cameras: {cameras}")
        return cameras

    def get_supported_resolutions(self, camera_index):
        """
        Tests a camera for a list of standard resolutions and returns the supported ones.
        """
        supported_resolutions = []
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logging.error(f"Could not open camera index {camera_index} to get resolutions.")
            return []

        for w, h in STANDARD_RESOLUTIONS:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual_w == w and actual_h == h:
                supported_resolutions.append(f"{w}x{h}")

        cap.release()
        logging.info(f"Supported resolutions for camera {camera_index}: {supported_resolutions}")
        return supported_resolutions

    def build(self):
        # The root is a FloatLayout to allow widget stacking
        root = FloatLayout()

        # The main layout for the camera view and controls
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # --- BANNER ---
        # To use a text banner:
        banner = Label(
            text="Happy 50th Birthday Laurie",
            font_size='32sp',
            size_hint_y=None,
            height=80
        )
        main_layout.add_widget(banner)

        # To use an image banner instead, comment out the Label code block above
        # and uncomment the Image code block below.
        #
        # banner = Image(
        #     source='banner.png', # Make sure banner.png is in the same directory
        #     size_hint_y=None,
        #     height=100,
        #     allow_stretch=True,
        #     keep_ratio=False
        # )
        # main_layout.add_widget(banner)
        # --- END BANNER ---

        self.camera_view = Image()
        main_layout.add_widget(self.camera_view)

        controls_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)

        self.available_cameras = self.get_available_cameras()
        if not self.available_cameras:
            logging.error("No cameras found!")
            return root

        camera_names = list(self.available_cameras.keys())
        self.camera_selector = Spinner(
            text=camera_names[0],
            values=camera_names,
        )
        self.camera_selector.bind(text=self.on_camera_select)
        controls_layout.add_widget(self.camera_selector)

        self.resolution_selector = Spinner(
            text="Resolution",
            values=[],
            size_hint_y=None,
            height=50
        )
        self.resolution_selector.bind(text=self.on_resolution_select)
        controls_layout.add_widget(self.resolution_selector)

        main_layout.add_widget(controls_layout)

        # Layout to center the round capture button
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        button_layout.add_widget(Widget()) # Left spacer
        self.capture_button = RoundButton(size_hint=(None, None), size=(80, 80))
        self.capture_button.bind(on_press=self.capture_photo)
        button_layout.add_widget(self.capture_button)
        button_layout.add_widget(Widget()) # Right spacer
        main_layout.add_widget(button_layout)

        # Add the main layout to the root
        root.add_widget(main_layout)

        # Create the flash widget, initially invisible
        self.flash = Widget(opacity=0)
        with self.flash.canvas:
            Color(1, 1, 1)
            self.flash_rect = Rectangle(size=self.flash.size, pos=self.flash.pos)
        self.flash.bind(size=self._update_flash_rect, pos=self._update_flash_rect)
        root.add_widget(self.flash)

        # Initial setup for the first camera
        first_camera_name = camera_names[0]
        self.update_camera(first_camera_name)

        Clock.schedule_interval(self.update, 1.0 / 30.0)

        return root

    def _update_flash_rect(self, instance, value):
        self.flash_rect.pos = instance.pos
        self.flash_rect.size = instance.size

    def update_camera(self, camera_name):
        """Central method to initialize or switch camera and its resolution."""
        selected_index = self.available_cameras[camera_name]
        logging.info(f"Switching to camera: {camera_name} (index: {selected_index})")

        if hasattr(self, 'capture') and self.capture.isOpened():
            self.capture.release()

        resolutions = self.get_supported_resolutions(selected_index)
        self.resolution_selector.values = resolutions
        if resolutions:
            self.resolution_selector.text = resolutions[-1] # Default to highest
            w, h = map(int, resolutions[-1].split('x'))
            self.capture = cv2.VideoCapture(selected_index)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            logging.info(f"Set camera {selected_index} to {w}x{h}")
        else:
            logging.warning(f"No supported resolutions found for camera {selected_index}. Using default.")
            self.capture = cv2.VideoCapture(selected_index)
            self.resolution_selector.text = 'Default'


    def on_camera_select(self, spinner, text):
        """Callback for when a new camera is selected."""
        self.update_camera(text)

    def on_resolution_select(self, spinner, text):
        """Callback for when a new resolution is selected."""
        if text == 'Default' or not hasattr(self, 'capture') or not self.capture.isOpened():
            return

        w, h = map(int, text.split('x'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        logging.info(f"Resolution changed to {w}x{h}")


    def update(self, dt):
        if not hasattr(self, 'capture') or not self.capture.isOpened():
            return

        ret, frame = self.capture.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            buf1 = cv2.flip(frame_rgb, 0)
            buf = buf1.tobytes()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.camera_view.texture = image_texture

    def do_flash(self):
        self.flash.opacity = 1
        Animation(opacity=0, duration=0.2).start(self.flash)

    def capture_photo(self, *args):
        if not hasattr(self, 'capture') or not self.capture.isOpened():
            logging.error("No camera is active to take a photo.")
            return

        if not os.path.exists("photos"):
            os.makedirs("photos")

        ret, frame = self.capture.read()
        if ret:
            now = datetime.now()
            filename = f"photos/photo_{now.strftime('%Y%m%d_%H%M%S')}.png"
            cv2.imwrite(filename, frame)
            logging.info(f"Photo saved as {filename}")
            self.do_flash()

    def on_stop(self):
        if hasattr(self, 'capture') and self.capture:
            self.capture.release()
            logging.info("Camera released.")

if __name__ == '__main__':
    CameraApp().run()
