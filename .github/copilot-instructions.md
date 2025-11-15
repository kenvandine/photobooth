# Photobooth Project - Copilot Instructions

## Project Overview

Photobooth is a full-screen, touch-friendly photobooth application created for Linux. The application displays a live camera view, allows users to capture photos, and includes customization options like custom banners and frames. The project also includes a REST API for photo management and is packaged as a Snap for easy distribution.

## Technology Stack

### Core Application
- **Python 3.12** - Primary programming language
- **Kivy 2.3.1** - UI framework for the photobooth application
- **OpenCV (cv2)** - Camera and image processing
- **GStreamer (via PyGObject)** - Media streaming backend
- **Pillow** - Image manipulation

### REST API
- **Flask** - Web framework for the REST API
- **pytest** - Testing framework

### Additional Components
- **OpenAI Whisper** - Voice recognition (voice_listener.py)
- **PyTorch** - ML backend for Whisper
- **Snap** - Packaging format for Linux distribution

## Project Structure

```
/
├── main.py                 # Main Kivy photobooth application
├── voice_listener.py       # Voice command listener using Whisper
├── create_assets.py        # Script to generate default assets (banners, frames, icons)
├── create_roku_icon.py     # Script to create Roku-specific icons
├── requirements.txt        # Python dependencies
├── assets/                 # Generated UI assets (banners, frames, icons)
├── photos/                 # Directory where captured photos are saved
├── restapi/
│   ├── api.py             # Flask REST API for photo management
│   ├── requirements.txt   # API-specific dependencies
│   ├── tests/
│   │   └── test_api.py   # pytest tests for the API
│   ├── react_frontend/   # React frontend for the API
│   ├── roku_app/         # Roku application
│   └── README.md         # API documentation
├── snap/
│   └── snapcraft.yaml    # Snap package configuration
└── files/                # Launcher scripts for snap packaging
```

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Python Version
- Target Python 3.12
- Use type hints where appropriate
- Leverage modern Python features (f-strings, pathlib, etc.)

### Dependencies
- Keep dependencies minimal and well-justified
- Pin major versions in requirements.txt
- Use virtual environments for development

## Building and Testing

### Initial Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate assets:**
   ```bash
   python create_assets.py
   ```
   This creates default banners, frames, and icons in the `assets/` directory.

### Running the Application

**Main Photobooth App:**
```bash
python main.py
```

**REST API:**
```bash
cd restapi
python api.py
```
The API will start on http://localhost:5000

### Testing

The project uses pytest for testing, primarily for the REST API:

```bash
# Run all tests
pytest restapi/tests/

# Run with verbose output
pytest -v restapi/tests/

# Run specific test file
pytest restapi/tests/test_api.py
```

**Note:** The main Kivy application (main.py) does not have automated tests due to its GUI nature.

### Linting

No formal linter is configured in the project. When adding code:
- Follow PEP 8 conventions
- Ensure code is readable and well-documented
- Match the existing code style in the file you're editing

### Building the Snap Package

```bash
snapcraft
```

This creates a `.snap` file that can be installed on Ubuntu and other Snap-supporting systems.

## Key Features and Components

### Main Application (main.py)
- Full-screen Kivy application
- Camera selection and resolution control
- Live camera preview using GStreamer
- Photo capture with flash effect
- Custom banner support via `CUSTOM_BANNER_PATH` environment variable
- Birthday frame overlay functionality
- Touch-friendly UI with custom-drawn buttons

### REST API (restapi/api.py)
- Photo upload via file or base64
- Metadata storage and retrieval
- Search functionality
- CRUD operations for photos
- Pagination support
- File validation and size limits (16MB max)

### Voice Listener (voice_listener.py)
- Uses OpenAI Whisper for speech recognition
- Listens for voice commands to trigger photo capture
- Runs as a separate component

## Configuration

### Environment Variables

- **`CUSTOM_BANNER_PATH`** - Path to a custom banner image
  - If not set, uses `assets/default_banner.png`
  - Example: `export CUSTOM_BANNER_PATH="/path/to/banner.png"`

- **`SNAP_COMMON`** - Base directory for Snap deployment
  - Used by the REST API to determine storage locations
  - Automatically set when running as a Snap

### Camera Configuration
- Camera selection is done via the UI dropdown
- Uses v4l2-ctl on Linux to detect and name cameras
- Resolution can be selected from supported camera resolutions

### API Configuration
- Upload folder: `api_photos/` (or `$SNAP_COMMON/api_photos`)
- Metadata folder: `photo_metadata/` (or `$SNAP_COMMON/photo_metadata`)
- Max file size: 16MB
- Allowed formats: png, jpg, jpeg, gif, bmp, webp

## Common Development Tasks

### Adding a New Feature to the Main App
1. Modify `main.py` - add the feature logic
2. Update UI elements if needed (Kivy widgets)
3. Test manually by running the application
4. Update README.md if it's a user-facing feature

### Adding a New API Endpoint
1. Add the endpoint handler in `restapi/api.py`
2. Write tests in `restapi/tests/test_api.py`
3. Run pytest to verify tests pass
4. Update `restapi/README.md` documentation

### Modifying Assets
1. Update `create_assets.py` script
2. Run `python create_assets.py` to regenerate
3. Verify assets appear correctly in the app

### Updating Dependencies
1. Update version in `requirements.txt`
2. Test that the app still works
3. Update snapcraft.yaml if needed for snap packaging

## Important Patterns

### Camera Handling
- Uses GStreamer pipeline for camera access
- Fallback to simpler methods if GStreamer fails
- Always check camera availability before use

### Photo Saving
- Photos saved to `photos/` directory
- Filename format: `photo_YYYYMMDD_HHMMSS.jpg`
- Includes metadata in REST API when uploaded

### Error Handling
- Log errors appropriately
- Provide user feedback for failures
- Graceful degradation when features unavailable

### UI Updates
- Use Kivy's Clock for scheduling UI updates
- Handle touch events with proper button behaviors
- Maintain responsive UI during operations

## Snap Packaging Notes

- Uses `core24` base
- Strict confinement with necessary plugs:
  - home, camera, network, audio-record, audio-playback
- Python venv created during build
- Launcher script wraps the main application

## Testing Philosophy

- REST API has comprehensive pytest coverage
- Main application testing is primarily manual due to GUI nature
- Focus on testing business logic and data operations
- UI testing done through manual verification

## Contributing Guidelines

When working on this project:
1. Make minimal, focused changes
2. Test changes thoroughly (automated for API, manual for UI)
3. Update documentation when adding features
4. Follow existing code style and patterns
5. Consider snap packaging implications for system-level changes
6. Verify camera functionality if modifying camera code
7. Test on Linux with actual camera hardware when possible

## Common Issues and Solutions

### Camera Not Detected
- Ensure v4l2-utils is installed on Linux
- Check camera permissions
- Verify GStreamer is properly installed

### Assets Missing
- Run `python create_assets.py` to generate default assets
- Check that `assets/` directory exists

### API Tests Failing
- Ensure test directories are cleaned up between runs
- Check that Flask test client is configured correctly
- Verify test isolation (each test should be independent)

### Snap Build Issues
- Ensure all dependencies are listed in requirements.txt
- Check that snapcraft.yaml has necessary stage-packages
- Verify file permissions and paths
