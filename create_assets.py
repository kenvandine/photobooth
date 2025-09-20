import os
import random
import logging
from PIL import Image as PILImage, ImageDraw

logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
DEFAULT_BANNER_PATH = 'assets/default_banner.png'
# --- END CONFIGURATION ---

def create_default_banner_if_needed():
    """
    Checks if a default banner image exists and creates one if it does not.

    The banner is a simple dark grey image created using Pillow and saved to
    the path specified by `DEFAULT_BANNER_PATH`. This ensures that the app
    has a visual banner even if a custom one is not provided.
    """
    if not os.path.exists('assets'):
        os.makedirs('assets')

    banner_path = DEFAULT_BANNER_PATH
    if not os.path.exists(banner_path):
        logging.info(f"Creating default banner at {banner_path}")
        width, height = 800, 100
        # Create a dark grey image using Pillow
        img = PILImage.new('RGB', (width, height), color = (50, 50, 50))
        img.save(banner_path)


def _get_random_point_in_border(width, height):
    """
    Gets a random (x, y) coordinate in the outer 15% of the image border.
    """
    border_w = width * 0.15
    border_h = height * 0.15

    # Decide which border to place the point in (top, bottom, left, right)
    side = random.choice(['top', 'bottom', 'left', 'right'])

    if side == 'top':
        x = random.randint(0, width)
        y = random.randint(0, int(border_h))
    elif side == 'bottom':
        x = random.randint(0, width)
        y = random.randint(int(height - border_h), height)
    elif side == 'left':
        x = random.randint(0, int(border_w))
        y = random.randint(0, height)
    else:  # right
        x = random.randint(int(width - border_w), width)
        y = random.randint(0, height)
    return x, y


def create_birthday_frames_if_needed():
    """
    Checks if birthday frame images exist and creates them if they do not.

    The frames are simple images with birthday-themed decorations, saved as
    PNG files in the `assets/frames/` directory. All frames only use the
    outer 20% of the image area.
    """
    frames_dir = 'assets/frames'
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)

    frame_paths = [os.path.join(frames_dir, f) for f in [
        'frame_confetti.png', 'frame_balloons.png', 'frame_stars.png'
    ]]
    width, height = 800, 600

    # Frame 1: Confetti
    if not os.path.exists(frame_paths[0]):
        logging.info(f"Creating confetti frame at {frame_paths[0]}")
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        colors = ["#FFD700", "#FF6347", "#00CED1", "#9370DB", "#32CD32"]
        for _ in range(500):
            x, y = _get_random_point_in_border(width, height)
            size = random.randint(3, 8)
            draw.ellipse([x, y, x + size, y + size], fill=random.choice(colors))
        img.save(frame_paths[0])

    # Frame 2: Balloons
    if not os.path.exists(frame_paths[1]):
        logging.info(f"Creating balloons frame at {frame_paths[1]}")
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        colors = ["#FF69B4", "#1E90FF", "#FFA500", "#FF4500"]
        for _ in range(25):
            x, y = _get_random_point_in_border(width, height)
            size = random.randint(20, 50)
            # Balloon shape
            draw.ellipse([x, y, x + size, y + size * 1.2], fill=random.choice(colors))
            # String
            draw.line([x + size / 2, y + size * 1.2, x + size / 2, y + size * 1.2 + 20], fill="grey")
        img.save(frame_paths[1])

    # Frame 3: Stars
    if not os.path.exists(frame_paths[2]):
        logging.info(f"Creating stars frame at {frame_paths[2]}")
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for _ in range(150):
            x, y = _get_random_point_in_border(width, height)
            size = random.randint(8, 25)
            # Simple star polygon
            draw.polygon([
                (x, y - size), (x + size * 0.3, y - size * 0.3), (x + size, y),
                (x + size * 0.3, y + size * 0.3), (x, y + size), (x - size * 0.3, y + size * 0.3),
                (x - size, y), (x - size * 0.3, y - size * 0.3)
            ], fill="yellow")
        img.save(frame_paths[2])


def create_change_frame_icon_if_needed():
    """
    Creates a simple icon for the frame-changing button if it doesn't exist.
    """
    icon_path = 'assets/change-frame.png'
    if not os.path.exists(icon_path):
        logging.info(f"Creating change frame icon at {icon_path}")
        width, height = 64, 64
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # A simple design: three colored squares
        colors = ["#FF5733", "#33FF57", "#3357FF"]
        draw.rectangle([10, 22, 30, 42], fill=colors[0])
        draw.rectangle([22, 10, 42, 30], fill=colors[1])
        draw.rectangle([34, 22, 54, 42], fill=colors[2])
        img.save(icon_path)

def create_accessories_if_needed():
    """
    Creates the accessory images if they don't exist.
    """
    if not os.path.exists('assets/accessories'):
        os.makedirs('assets/accessories')

    hat_path = 'assets/accessories/hat.png'
    if not os.path.exists(hat_path):
        logging.info(f"Creating hat image at {hat_path}")
        width, height = 100, 50
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 20, 90, 30], fill="black")
        draw.rectangle([30, 0, 70, 20], fill="black")
        img.save(hat_path)

    glasses_path = 'assets/accessories/glasses.png'
    if not os.path.exists(glasses_path):
        logging.info(f"Creating glasses image at {glasses_path}")
        width, height = 100, 30
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, 40, 30], outline="black", width=3)
        draw.ellipse([60, 0, 100, 30], outline="black", width=3)
        draw.line([40, 15, 60, 15], fill="black", width=3)
        img.save(glasses_path)

def create_accessories_icon_if_needed():
    """
    Creates a simple icon for the accessories button if it doesn't exist.
    """
    icon_path = 'assets/accessories_icon.png'
    if not os.path.exists(icon_path):
        logging.info(f"Creating accessories icon at {icon_path}")
        width, height = 64, 64
        img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # A simple design: a top hat and glasses
        # Hat
        draw.rectangle([16, 10, 48, 20], fill="black")
        draw.rectangle([24, 20, 40, 30], fill="black")
        # Glasses
        draw.ellipse([10, 35, 30, 50], outline="black", width=3)
        draw.ellipse([34, 35, 54, 50], outline="black", width=3)
        draw.line([30, 42, 34, 42], fill="black", width=3)
        img.save(icon_path)

if __name__ == '__main__':
    create_default_banner_if_needed()
    create_birthday_frames_if_needed()
    create_change_frame_icon_if_needed()
    create_accessories_icon_if_needed()
    create_accessories_if_needed()
    logging.info("All assets created successfully.")
