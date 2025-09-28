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

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

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
import threading
import queue
import numpy as np
import time
VOICE_ENABLED = os.environ.get('VOICE_ENABLED')
if VOICE_ENABLED:
    from voice_listener import VoiceListener
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
DEFAULT_BANNER_PATH = 'assets/default_banner.png'
PHOTOBOOTH_URL = os.environ.get('PHOTOBOOTH_URL')
RESOLUTION = os.environ.get('RESOLUTION')
# --- END CONFIGURATION ---

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


class GlibMainLoopWorker(threading.Thread):
    """A worker thread that runs the GLib.MainLoop."""
    def __init__(self, **kwargs):
        super(GlibMainLoopWorker, self).__init__(**kwargs)
        self.main_loop = GLib.MainLoop()

    def run(self):
        logging.info("GLib main loop worker started.")
        self.main_loop.run()
        logging.info("GLib main loop worker stopped.")

    def stop(self):
        if self.main_loop.is_running():
            self.main_loop.quit()

class FrameProcessorWorker(threading.Thread):
    """A worker thread to process GStreamer frames."""
    def __init__(self, app, **kwargs):
        super(FrameProcessorWorker, self).__init__(**kwargs)
        self.app = app
        self.stop_event = threading.Event()

    def run(self):
        logging.info("Frame processor worker started.")
        while not self.stop_event.is_set():
            try:
                sample = self.app.sample_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if sample:
                buf = sample.get_buffer()
                caps = sample.get_caps()
                h = caps.get_structure(0).get_value("height")
                w = caps.get_structure(0).get_value("width")

                success, map_info = buf.map(Gst.MapFlags.READ)
                if success:
                    frame = np.ndarray((h, w, 3), buffer=map_info.data, dtype=np.uint8)

                    # The frame from GStreamer is BGR. _apply_overlay expects BGR.
                    processed_frame = self.app._apply_overlay(frame.copy())
                    self.app.latest_processed_frame = processed_frame

                    try:
                        self.app.display_queue.put_nowait(processed_frame)
                    except queue.Full:
                        pass # UI is lagging

                    buf.unmap(map_info)
        logging.info("Frame processor worker stopped.")

    def stop(self):
        self.stop_event.set()

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
        self.resized_overlay = None
        self.pipeline = None
        self.glib_worker = None
        self.frame_processor_worker = None
        self.sample_queue = queue.Queue(maxsize=5)  # Raw samples from GStreamer
        self.display_queue = queue.Queue(maxsize=2) # Processed frames for the UI
        self.latest_processed_frame = None          # For photo capture

    def get_available_cameras(self):
        """
        Detects and lists available video cameras on the system.
        """
        cameras = {}
        # Iterate through the first 10 /dev/video nodes
        for i in range(10):
            device_path = f"/dev/video{i}"
            if os.path.exists(device_path):
                try:
                    # Check if the device is a video capture device
                    result = subprocess.run(
                        ['v4l2-ctl', '-d', device_path, '--query-cap'],
                        check=True, capture_output=True, text=True
                    )
                    if "Video Capture" in result.stdout:
                        cameras[f"Camera {i}"] = {'index': i, 'type': 'v4l2'}
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback for systems without v4l2-ctl or for non-v4l2 devices
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        cameras[f"Camera {i}"] = {'index': i, 'type': 'default'}
                        cap.release()
            else:
                # No more video devices
                break
        logging.info(f"Available cameras: {cameras}")
        return cameras

    def get_supported_resolutions(self, camera_index):
        """
        Determines the supported resolutions, pixel formats, and framerates for a given camera.
        It uses `v4l2-ctl` to get a reliable list of format/resolution/framerate combinations.
        If that fails, it falls back to a basic OpenCV-based trial-and-error method.

        Args:
            camera_index (int): The index of the camera to check.

        Returns:
            list: A sorted list of (width, height, format_str, framerate) tuples.
                  Returns an empty list if no formats can be determined.
        """
        # Try to get formats using v4l2-ctl for reliability
        device_path = f"/dev/video{camera_index}"
        try:
            # Ensure v4l2-ctl is installed
            subprocess.run(['which', 'v4l2-ctl'], check=True, capture_output=True)

            # Get the output from v4l2-ctl
            result = subprocess.run(
                ['v4l2-ctl', '-d', device_path, '--list-formats-ext'],
                check=True, capture_output=True, text=True,
                errors='ignore'
            )
            output = result.stdout
            logging.info(f"v4l2-ctl output for {device_path}:\n{output}")

            formats = []
            format_pattern = re.compile(r"\[\d+\]:\s+'(\w+)'")
            resolution_pattern = re.compile(r'\s+Size: Discrete\s+(\d+)x(\d+)')
            framerate_pattern = re.compile(r'\s+Interval: Discrete .* \((\d+\.\d+)\s+fps\)')

            # Split output into blocks for each format
            format_blocks = re.split(r'(?=\[\d+\]:)', output)

            for block in format_blocks:
                if not block.strip():
                    continue

                format_match = format_pattern.search(block)
                if not format_match:
                    continue
                current_format = format_match.group(1)

                # Split each format block by resolution
                resolution_blocks = re.split(r'(?=\s+Size: Discrete)', block)

                for res_block in resolution_blocks:
                    if not res_block.strip() or "Size: Discrete" not in res_block:
                        continue

                    resolution_match = resolution_pattern.search(res_block)
                    if not resolution_match:
                        continue

                    w = int(resolution_match.group(1))
                    h = int(resolution_match.group(2))

                    framerate_matches = framerate_pattern.finditer(res_block)
                    for fr_match in framerate_matches:
                        fps = float(fr_match.group(1))
                        formats.append((w, h, current_format, int(fps)))

            if formats:
                # Remove duplicates and sort the formats
                formats = sorted(list(set(formats)), key=lambda f: (f[0] * f[1], f[3]))
                logging.info(f"Found formats for {device_path} via v4l2-ctl: {formats}")
                return formats
            else:
                logging.warning(f"v4l2-ctl for {device_path} gave no resolution/format output. "
                                "Falling back to OpenCV's trial-and-error method.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.warning(f"v4l2-ctl for {device_path} failed (is it installed?): {e}. "
                            "Falling back to OpenCV's trial-and-error method.")

        # Fallback to OpenCV's trial-and-error method
        supported_formats = []
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            logging.error(f"Could not open camera index {camera_index} for fallback resolution check.")
            return []

        # Add the user-specified resolution to the list to ensure it is checked
        resolutions_to_check = STANDARD_RESOLUTIONS[:] # Make a copy
        if self.resolution:
            try:
                w, h = map(int, self.resolution.split('x'))
                if (w, h) not in resolutions_to_check:
                    resolutions_to_check.append((w, h))
            except (ValueError, TypeError):
                logging.error(f"Invalid resolution format: {self.resolution}")

        for w, h in resolutions_to_check:
            # Set the desired resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

            # Allow some time for the setting to apply
            time.sleep(0.2)

            # Read the actual resolution back from the camera
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            logging.info(f"Testing {w}x{h}, got {actual_w}x{actual_h}")
            # Check if the camera accepted the resolution
            if actual_w == w and actual_h == h:
                # Can't determine format or framerate here, so use a sensible default
                if (w, h, 'YUYV', 30) not in supported_formats:
                    supported_formats.append((w, h, 'YUYV', 30))

        cap.release()

        if supported_formats:
            supported_formats.sort(key=lambda f: (f[0] * f[1], f[3]))
            logging.info(f"Supported formats for camera {camera_index} (OpenCV fallback): {supported_formats}")
        else:
            logging.warning(f"OpenCV fallback could not determine any supported resolutions for camera {camera_index}.")

        return supported_formats

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
        self.available_cameras = self.get_available_cameras()

        if not self.available_cameras:
            logging.error("No cameras found!")
            # Optionally, display a message to the user in the UI
            return root

        camera_names = list(self.available_cameras.keys())
        initial_camera_name = camera_names[0]  # Default to the first camera

        if self.device is not None:
            # If a device index is specified, try to find the corresponding camera name
            found = False
            for name, info in self.available_cameras.items():
                if info['index'] == self.device:
                    initial_camera_name = name
                    found = True
                    break
            if not found:
                logging.warning(f"Device index {self.device} not found or is not available. "
                                f"Falling back to default camera.")

        # Spinner for resolution selection (will be moved to a popup)
        self.resolution_selector = Spinner(text="Resolution", values=[], size_hint_y=None, height=50)
        self.resolution_selector.bind(text=self.on_resolution_select)

        # Layout for the capture button, centered horizontally
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        button_layout.add_widget(Widget())  # Left spacer
        self.capture_button = RoundButton(size_hint=(None, None), size=(240, 240))
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
            size=(128, 128),
            pos_hint={'x': 0.05, 'y': 0.05}
        )
        self.camera_switch_button.bind(on_press=self.open_camera_selector)
        root.add_widget(self.camera_switch_button)

        # A button to change the birthday frame
        self.frame_switch_button = RoundImageButton(
            source='assets/change-frame.png',
            size_hint=(None, None),
            size=(128, 128),
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

        # Start the GLib main loop in a separate thread
        self.glib_worker = GlibMainLoopWorker()
        self.glib_worker.start()

        # Start the frame processor worker
        self.frame_processor_worker = FrameProcessorWorker(self)
        self.frame_processor_worker.start()

        # Initialize with the selected or default camera
        self.update_camera(initial_camera_name)

        # Schedule the UI update from the processed frames queue
        Clock.schedule_interval(self.update, 1/60.0)

        # Create a Kivy-safe trigger for capturing a photo
        self.capture_trigger = Clock.create_trigger(self.capture_photo)

        # Initialize and start the voice listener if enabled
        if VOICE_ENABLED:
            try:
                self.voice_listener = VoiceListener(callback=self.capture_trigger)
                self.voice_listener.start()
            except Exception as e:
                logging.error(f"Failed to start voice listener: {e}")
                self.voice_listener = None
        else:
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

    def on_new_sample(self, sink):
        """Callback for GStreamer's appsink. Puts the raw sample on a queue."""
        sample = sink.emit("pull-sample")
        if sample:
            try:
                # This is called from a GStreamer thread, so we push to a queue
                # to be processed by our worker thread.
                self.sample_queue.put_nowait(sample)
            except queue.Full:
                pass  # Drop frame if the processing thread is lagging
        return Gst.FlowReturn.OK

    def update_camera(self, camera_name):
        """
        Switches the active camera by building and launching a GStreamer pipeline.
        """
        camera_info = self.available_cameras[camera_name]
        selected_index = camera_info['index']
        logging.info(f"Switching to camera: {camera_name} (index: {selected_index})")

        # Stop any existing pipeline
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            logging.info("Stopped previous GStreamer pipeline.")

        # Get a list of available formats (width, height, pixel_format, framerate)
        self.supported_formats = self.get_supported_resolutions(selected_index)

        # Populate the spinner with human-readable options
        self.resolution_selector.values = [f"{w}x{h} ({f}) @ {fps}fps" for w, h, f, fps, in self.supported_formats]

        # Select the best format to use (highest resolution, prefer MJPG, highest framerate)
        w, h, pixel_format, framerate = (1920, 1080, 'MJPG', 30) # Sensible default
        if self.supported_formats:
            # The list is sorted by resolution, then framerate. The last item is the best.
            w, h, pixel_format, framerate = self.supported_formats[-1]

            # But, we prefer MJPG for high resolutions if available at the same res/fps.
            for f_w, f_h, f_fmt, f_fps in reversed(self.supported_formats):
                if (f_w, f_h, f_fps) == (w, h, framerate) and f_fmt == 'MJPG':
                    pixel_format = 'MJPG'
                    break

            self.resolution_selector.text = f"{w}x{h} ({pixel_format}) @ {framerate}fps"
            logging.info(f"Selected best format: {w}x{h}, {pixel_format} @ {framerate}fps")
        else:
            logging.error("No supported formats found. Falling back to default.")
            self.resolution_selector.text = "Default"

        # Programmatically build the GStreamer pipeline
        self.pipeline = Gst.Pipeline.new("camera-pipeline")
        source = Gst.ElementFactory.make("v4l2src", "source")
        source.set_property("device", f"/dev/video{selected_index}")

        # Create the initial caps filter based on the camera's format
        if pixel_format == 'MJPG':
            caps_str = f"image/jpeg,width={w},height={h},framerate={framerate}/1"
            caps = Gst.Caps.from_string(caps_str)
            caps_filter = Gst.ElementFactory.make("capsfilter", "caps_filter")
            caps_filter.set_property("caps", caps)
            decoder = Gst.ElementFactory.make("jpegdec", "decoder")
        else: # Assuming YUYV or other raw formats
            caps_str = f"video/x-raw,format=YUY2,width={w},height={h},framerate={framerate}/1"
            caps = Gst.Caps.from_string(caps_str)
            caps_filter = Gst.ElementFactory.make("capsfilter", "caps_filter")
            caps_filter.set_property("caps", caps)
            decoder = None # No decoder needed for raw formats

        videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")

        # Final caps filter to ensure the stream is in BGR format for OpenCV
        final_caps = Gst.Caps.from_string("video/x-raw,format=BGR")
        final_caps_filter = Gst.ElementFactory.make("capsfilter", "final_caps_filter")
        final_caps_filter.set_property("caps", final_caps)

        sink = Gst.ElementFactory.make("appsink", "sink")
        sink.set_property("emit-signals", True)
        sink.set_property("max-buffers", 1) # We only need the latest frame
        sink.set_property("drop", True)
        sink.connect("new-sample", self.on_new_sample)

        # Add elements to the pipeline
        elements = [source, caps_filter, videoconvert, final_caps_filter, sink]
        if decoder:
            elements.insert(2, decoder)

        for el in elements:
            self.pipeline.add(el)

        # Link elements
        source.link(caps_filter)
        if decoder:
            caps_filter.link(decoder)
            decoder.link(videoconvert)
        else:
            caps_filter.link(videoconvert)
        videoconvert.link(final_caps_filter)
        final_caps_filter.link(sink)

        # Start the pipeline
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logging.error("Unable to set the pipeline to the playing state.")
            return

        logging.info("GStreamer pipeline started successfully.")

        # The worker threads are already running. The pipeline will start
        # pushing frames to the sample_queue.

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
        self.resized_overlay = None

        # Clear the queue of any stale frames to ensure the new frame is shown
        while not self.display_queue.empty():
            try:
                self.display_queue.get_nowait()
            except queue.Empty:
                break
        logging.info(f"Changed birthday frame to: {frame_path}")

    def on_resolution_select(self, spinner, text):
        """
        Event handler for resolution selection from the spinner.

        Args:
            spinner: The spinner instance.
            text (str): The selected resolution string (e.g., "1920x1080").
        """
        if text == 'Default' or not hasattr(self, 'pipeline') or not self.pipeline:
            return

        # This is a bit of a hack. We're assuming the format of the text is "WxH (FORMAT) @ FPSfps"
        # and we only care about the WxH part. A more robust solution would parse this properly.
        try:
            res_part = text.split(' ')[0]
            w, h = map(int, res_part.split('x'))

            # Find the full format details from the supported_formats list
            selected_format = None
            for f in self.supported_formats:
                if f[0] == w and f[1] == h and f"{f[0]}x{f[1]}" in text:
                    selected_format = f
                    break

            if selected_format:
                logging.info(f"Resolution selected: {selected_format}")
                # We need to rebuild the pipeline for the new resolution
                # For now, we'll just log this. A full implementation would
                # tear down the old pipeline and build a new one.
                # NOTE: This is a simplified version and might not work in all cases.
                self.update_camera(self.camera_selector.text)
            else:
                logging.error(f"Could not find matching format for selection: {text}")

        except Exception as e:
            logging.error(f"Error processing resolution selection '{text}': {e}")


    def _apply_overlay(self, frame):
        """
        Applies the birthday frame overlay to a given frame.
        """
        if self.birthday_frame is None:
            return frame

        h, w, _ = frame.shape
        if self.resized_overlay is None or self.resized_overlay.shape[:2] != (h, w):
            logging.info(f"Creating new overlay cache for resolution {w}x{h}.")
            self.resized_overlay = cv2.resize(self.birthday_frame, (w, h))

        overlay_img = self.resized_overlay[:,:,0:3] # BGR channels
        mask = self.resized_overlay[:,:,3] # Alpha channel

        # Black-out the area of the overlay in the background frame
        background = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))

        # Take only the region of the overlay image.
        foreground = cv2.bitwise_and(overlay_img, overlay_img, mask=mask)

        # Add the two images together
        return cv2.add(background, foreground)

    def update(self, dt):
        """
        Updates the camera view with the latest frame from the display queue.
        This method is called repeatedly by the Kivy Clock.
        """
        try:
            # Get the most recent frame, discard older ones
            frame = self.display_queue.get_nowait()
            while not self.display_queue.empty():
                try:
                    frame = self.display_queue.get_nowait()
                except queue.Empty:
                    break
        except queue.Empty:
            return  # No new frame to display

        # The frame from the queue is already processed and in BGR format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        buf = cv2.flip(frame_rgb, 0).tobytes()

        image_texture = Texture.create(
            size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb'
        )
        image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
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
        Captures a photo from the latest processed frame, saves it, and uploads it.
        """
        if self.latest_processed_frame is None:
            logging.error("No frame available to take a photo.")
            return

        # Create the 'photos' directory if it doesn't exist
        if not os.path.exists("photos"):
            os.makedirs("photos")

        # The latest_processed_frame is already processed with an overlay
        frame_with_overlay = self.latest_processed_frame

        now = datetime.now()
        filename = f"photos/photo_{now.strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, frame_with_overlay)
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
        Cleanly stops worker threads and the GStreamer pipeline
        when the application is closed.
        """
        logging.info("Stopping application...")
        if hasattr(self, 'voice_listener') and self.voice_listener:
            self.voice_listener.stop()

        # Stop the frame processor worker first
        if self.frame_processor_worker:
            self.frame_processor_worker.stop()
            self.frame_processor_worker.join()
            logging.info("Frame processor worker stopped.")

        # Stop the GStreamer pipeline
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            logging.info("GStreamer pipeline state set to NULL.")

        # Stop the GLib main loop
        if self.glib_worker:
            self.glib_worker.stop()
            self.glib_worker.join()
            logging.info("GLib main loop worker stopped.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A Kivy-based camera app.")
    parser.add_argument('--device', help='The v4l device path to use (e.g., /dev/video0)')
    args = parser.parse_args()
    device_path = args.device
    device_index = None
    if device_path:
        # Try to extract a numeric index from the end of the string,
        # as cv2.VideoCapture prefers integer indices on Linux.
        match = re.search(r'\d+$', device_path)
        if match:
            device_index = int(match.group(0))
        else:
            logging.warning(f"Could not extract a numeric index from device path: '{device_path}'. "
                            "The application will use the default camera.")

    app = CameraApp(device=device_index, resolution=RESOLUTION)
    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()