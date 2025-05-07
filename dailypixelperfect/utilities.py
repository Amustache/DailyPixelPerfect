import os

from PIL import Image, ImageDraw

BASEDIR = os.path.abspath(os.path.dirname(__file__))

def escape_for_telegram(text):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(c, f"\\{c}")
    return text

def generate_pixels(size=1, number=0, filename="pixel.png"):
    """
    Method to create a single image
    """
    if size > 10:
        raise ValueError("size too big")

    if number < 0 or number > 2 ** (size * size) - 1:
        raise ValueError("number wrong")

    numbin = bin(number)[2:].zfill(size * size)

    img = Image.new('RGB', (size, size), color='white')
    pixels = img.load()
    for i in range(size):
        for j in range(size):
            pixels[j, i] = (0, 0, 0) if numbin[j + i * size] == '1' else (255, 255, 255)

    img.resize((512, 512), Image.NEAREST).save(filename)
