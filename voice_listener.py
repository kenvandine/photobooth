import threading
import whisper
import sounddevice as sd
import numpy as np
import queue
import logging

class VoiceListener:
    """
    A class to listen for a specific keyword using the Whisper ASR model.

    This class runs in a separate thread, continuously recording audio from the
    microphone, transcribing it, and checking for a keyword. When the keyword
    is detected, it invokes a callback function.
    """
    def __init__(self, callback, model="tiny.en", keyword="smile"):
        """
        Initializes the VoiceListener.

        Args:
            callback: The function to call when the keyword is detected.
            model (str): The name of the Whisper model to use (e.g., "tiny.en").
            keyword (str): The keyword to listen for.
        """
        self.callback = callback
        self.model_name = model
        self.keyword = keyword.lower()
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.samplerate = 16000  # Whisper requires 16kHz sample rate

    def _record_callback(self, indata, frames, time, status):
        """
        This callback is called by sounddevice for each new audio chunk.
        """
        if status:
            logging.warning(f"Sounddevice status: {status}")
        self.audio_queue.put(indata.copy())

    def _run(self):
        """
        The main loop for the voice listener thread.
        """
        try:
            logging.info(f"Loading whisper model '{self.model_name}'...")
            model = whisper.load_model(self.model_name)
            logging.info("Whisper model loaded.")
        except Exception as e:
            logging.error(f"Failed to load whisper model: {e}")
            return

        # Use a context manager for the audio stream to ensure it's closed properly
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='float32', callback=self._record_callback):
                logging.info(f"Voice listener started. Listening for '{self.keyword}'...")

                # Accumulate audio data for a few seconds before transcribing
                audio_buffer = np.array([], dtype=np.float32)

                while not self.stop_event.is_set():
                    try:
                        # Get audio data from the queue
                        audio_chunk = self.audio_queue.get(timeout=1)
                        audio_buffer = np.concatenate((audio_buffer, audio_chunk.flatten()))

                        # Transcribe when we have a few seconds of audio
                        # This is a trade-off between responsiveness and accuracy
                        if len(audio_buffer) >= int(self.samplerate * 1.5):
                            # Transcribe the audio buffer
                            result = model.transcribe(audio_buffer, fp16=False) # fp16=False if not using GPU
                            transcript = result['text'].lower()
                            logging.info(f"Transcription: '{transcript}'")

                            # Check if the keyword is in the transcript
                            if self.keyword in transcript:
                                logging.info(f"Keyword '{self.keyword}' detected! Triggering callback.")
                                self.callback()

                            # Clear the buffer after transcription
                            audio_buffer = np.array([], dtype=np.float32)

                    except queue.Empty:
                        # This is expected when there's no audio
                        continue
                    except Exception as e:
                        logging.error(f"Error in voice listener loop: {e}")
                        # Clear buffer on error to prevent repeated issues
                        audio_buffer = np.array([], dtype=np.float32)

        except Exception as e:
            logging.error(f"Failed to open audio stream: {e}")

        logging.info("Voice listener stopped.")

    def start(self):
        """Starts the voice listener thread."""
        logging.info("Starting voice listener thread...")
        self.stop_event.clear()
        self.thread.start()

    def stop(self):
        """Stops the voice listener thread."""
        logging.info("Stopping voice listener thread...")
        self.stop_event.set()
        # Wait for the thread to finish
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        logging.info("Voice listener thread stopped.")
