# utils/background_remover.py
from rembg import remove
from PIL import Image
import os
from typing import Union

def remove_background_from_pil(img, output_path: str = None):
    """
    img: PIL.Image (RGBA veya RGB)
    output_path: kaydetmek istersen
    returns: PIL.Image (RGBA) - arka planı kaldırılmış
    """
    result = remove(img)
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.save(output_path)
    return result

def remove_background_from_path(input_path: str, output_path: str = None):
    img = Image.open(input_path).convert("RGBA")
    return remove_background_from_pil(img, output_path)
