import os
from PIL import Image, ImageDraw, ImageFont
import logging

logging.basicConfig(level=logging.INFO)

def create_roku_channel_icon():
    """
    Creates the HD channel icon required by the Roku manifest.
    """
    icon_dir = 'roku_app/images'
    icon_path = os.path.join(icon_dir, 'channel-icon-hd.png')
    width, height = 336, 210

    # Create the directory if it doesn't exist
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)

    # Create a new image with a dark grey background
    img = Image.new('RGB', (width, height), color = (60, 60, 60))
    draw = ImageDraw.Draw(img)

    # Add some text
    try:
        # Use a default font
        font = ImageFont.load_default()
    except IOError:
        # If default font is not available, draw simple text
        font = None

    text = "Photo Slideshow"

    # Calculate text size to center it
    if font:
        try:
            # The modern way to get text size
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except AttributeError:
            # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)

        text_x = (width - text_width) / 2
        text_y = (height - text_height) / 2
        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
    else:
        # Fallback if font loading fails
        draw.text((80, 95), text, fill=(255, 255, 255))


    # Save the image
    img.save(icon_path)
    logging.info(f"Roku channel icon created at {icon_path}")

if __name__ == '__main__':
    create_roku_channel_icon()
