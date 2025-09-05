import kivy
kivy.require('2.3.1')

from kivy.app import App
from kivy.animation import Animation
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
from datetime import datetime
import logging
import subprocess
import re
from PIL import Image as PILImage, ImageDraw

logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
DEFAULT_BANNER_PATH = 'assets/default_banner.png'
# --- END CONFIGURATION ---

# A list of common resolutions to test
STANDARD_RESOLUTIONS = [
    (640, 480),
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1920, 1080),
    (3840, 2160)
]

def create_default_banner_if_needed():
    """Checks for the default banner and creates it if it's missing."""
    if not os.path.exists('assets'):
        os.makedirs('assets')

    banner_path = DEFAULT_BANNER_PATH
    if not os.path.exists(banner_path):
        logging.info(f"Creating default banner at {banner_path}")
        width, height = 800, 100
        # Create a dark grey image using Pillow
        img = PILImage.new('RGB', (width, height), color = (50, 50, 50))
        img.save(banner_path)


class RoundButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super(RoundButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        with self.canvas.before:
            Color(0.4, 0.4, 0.4, 1)
            self.ring = Ellipse()
            Color(0.7, 0.7, 0.7, 1)
            self.circle = Ellipse()
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.update_graphics()

    def update_graphics(self, *args):
        self.ring.pos = self.pos
        self.ring.size = self.size
        inner_size = self.width * 0.8
        inner_pos_x = self.x + (self.width - inner_size) / 2
        inner_pos_y = self.y + (self.height - inner_size) / 2
        self.circle.pos = (inner_pos_x, inner_pos_y)
        self.circle.size = (inner_size, inner_size)

    def on_state(self, widget, value):
        if value == 'down':
            with self.canvas.after:
                Color(0, 0, 0, 0.2)
                self.feedback = Ellipse(pos=self.pos, size=self.size)
        else:
            if hasattr(self, 'feedback'):
                self.canvas.after.remove(self.feedback)


class RoundImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(RoundImageButton, self).__init__(**kwargs)
        with self.canvas.before:
            self.stencil = StencilPush()
            self.stencil_shape = Ellipse()
        with self.canvas.after:
            self.stencil_pop = StencilPop()

        self.bind(pos=self.update_stencil, size=self.update_stencil)

    def update_stencil(self, *args):
        self.stencil_shape.pos = self.pos
        self.stencil_shape.size = self.size


class CameraApp(App):

    def get_available_cameras(self):
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
        root = FloatLayout()
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

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

        self.camera_view = Image()
        main_layout.add_widget(self.camera_view)

        self.available_cameras = self.get_available_cameras()
        if not self.available_cameras:
            logging.error("No cameras found!")
            return root

        camera_names = list(self.available_cameras.keys())

        self.resolution_selector = Spinner(text="Resolution", values=[], size_hint_y=None, height=50)
        self.resolution_selector.bind(text=self.on_resolution_select)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        button_layout.add_widget(Widget())
        self.capture_button = RoundButton(size_hint=(None, None), size=(80, 80))
        self.capture_button.bind(on_press=self.capture_photo)
        button_layout.add_widget(self.capture_button)
        button_layout.add_widget(Widget())
        main_layout.add_widget(button_layout)

        root.add_widget(main_layout)

        self.camera_switch_button = RoundImageButton(
            source='assets/system-settings.png',
            size_hint=(None, None),
            size=(32, 32),
            pos_hint={'x': 0.05, 'y': 0.05}
        )
        self.camera_switch_button.bind(on_press=self.open_camera_selector)
        root.add_widget(self.camera_switch_button)

        self.flash = Widget(opacity=0)
        with self.flash.canvas:
            Color(1, 1, 1)
            self.flash_rect = Rectangle(size=self.flash.size, pos=self.flash.pos)
        self.flash.bind(size=self._update_flash_rect, pos=self._update_flash_rect)
        root.add_widget(self.flash)

        first_camera_name = camera_names[0]
        self.update_camera(first_camera_name)

        Clock.schedule_interval(self.update, 1.0 / 30.0)

        return root

    def _update_flash_rect(self, instance, value):
        self.flash_rect.pos = instance.pos
        self.flash_rect.size = instance.size

    def update_camera(self, camera_name):
        selected_index = self.available_cameras[camera_name]
        logging.info(f"Switching to camera: {camera_name} (index: {selected_index})")

        if hasattr(self, 'capture') and self.capture.isOpened():
            self.capture.release()

        resolutions = self.get_supported_resolutions(selected_index)
        self.resolution_selector.values = resolutions
        if resolutions:
            self.resolution_selector.text = resolutions[-1]
            w, h = map(int, resolutions[-1].split('x'))
            self.capture = cv2.VideoCapture(selected_index)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            logging.info(f"Set camera {selected_index} to {w}x{h}")
        else:
            logging.warning(f"No supported resolutions found for camera {selected_index}. Using default.")
            self.capture = cv2.VideoCapture(selected_index)
            self.resolution_selector.text = 'Default'

    def on_camera_select(self, camera_name):
        self.update_camera(camera_name)

    def open_camera_selector(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup = Popup(title='Camera & Resolution', content=content, size_hint=(0.8, 0.9))

        # Add camera selection
        content.add_widget(Label(text='Cameras', size_hint_y=None, height=40))
        for camera_name in self.available_cameras.keys():
            btn = Button(text=camera_name, size_hint_y=None, height=50)
            btn.bind(on_release=lambda x, name=camera_name: self.select_camera_and_close(name, popup))
            content.add_widget(btn)

        # Add resolution selection
        content.add_widget(Label(text='Resolution', size_hint_y=None, height=40))
        if self.resolution_selector.parent:
            self.resolution_selector.parent.remove_widget(self.resolution_selector)
        content.add_widget(self.resolution_selector)

        def cleanup_on_dismiss(popup_instance):
            if self.resolution_selector.parent:
                self.resolution_selector.parent.remove_widget(self.resolution_selector)
        popup.bind(on_dismiss=cleanup_on_dismiss)

        # Add a close button to the popup for abandoning selection
        close_button = Button(text='Close', size_hint_y=None, height=50)
        close_button.bind(on_release=popup.dismiss)
        content.add_widget(close_button)

        popup.open()

    def select_camera_and_close(self, camera_name, popup):
        self.on_camera_select(camera_name)
        popup.dismiss()

    def on_resolution_select(self, spinner, text):
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
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
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
    create_default_banner_if_needed()
    CameraApp().run()
