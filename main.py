import kivy
kivy.require('2.3.1') # replace with your Kivy version if necessary

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class CameraApp(App):

    def get_available_cameras(self):
        """Detect and return a list of available camera indices."""
        available_cameras = []
        # Check for cameras from index 0 to 9
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(str(i))
                cap.release()
        logging.info(f"Available cameras: {available_cameras}")
        return available_cameras

    def build(self):
        self.layout = BoxLayout(orientation='vertical')

        self.camera_view = Image()
        self.layout.add_widget(self.camera_view)

        # Camera selection dropdown
        self.available_cameras = self.get_available_cameras()
        if not self.available_cameras:
            logging.error("No cameras found!")
            # Handle no camera case - maybe show a placeholder or a message
            # For now, the app will probably fail later on, which is acceptable for this task
            return self.layout

        self.camera_selector = Spinner(
            text=f"Camera {self.available_cameras[0]}",
            values=[f"Camera {i}" for i in self.available_cameras],
            size_hint_y=None,
            height=50
        )
        self.camera_selector.bind(text=self.on_camera_select)
        self.layout.add_widget(self.camera_selector)

        self.capture_button = Button(text="Take Photo", size_hint_y=None, height=100)
        self.capture_button.bind(on_press=self.capture_photo)
        self.layout.add_widget(self.capture_button)

        # Initialize capture with the first available camera
        self.capture = cv2.VideoCapture(int(self.available_cameras[0]))
        logging.info(f"Starting with camera index: {self.available_cameras[0]}")

        Clock.schedule_interval(self.update, 1.0 / 30.0)

        return self.layout

    def on_camera_select(self, spinner, text):
        """Callback for when a new camera is selected."""
        selected_index = text.split(" ")[-1]
        logging.info(f"Switching to camera index: {selected_index}")
        if self.capture:
            self.capture.release()
        self.capture = cv2.VideoCapture(int(selected_index))


    def update(self, dt):
        if not hasattr(self, 'capture') or not self.capture.isOpened():
            return

        ret, frame = self.capture.read()
        if ret:
            # The frame is typically in BGR format, Kivy texture needs RGB
            # Also, flipping is often necessary
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            buf1 = cv2.flip(frame_rgb, 0)
            buf = buf1.tobytes()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='rgb') # Changed to rgb
            image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.camera_view.texture = image_texture

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

    def on_stop(self):
        if hasattr(self, 'capture') and self.capture:
            self.capture.release()
            logging.info("Camera released.")

if __name__ == '__main__':
    CameraApp().run()
