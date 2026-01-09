# utils/image_downloader.py
from PIL import Image
from io import BytesIO
import os
import requests

def download_image(url: str, save_path: str = None, timeout: int = 10, max_retries: int = 3) -> Image.Image:
    """
    URL veya yerel dosya yolundan bir görüntü yükler.
    Eğer URL verilirse internetten indirir.
    Eğer yerel dosya yolu verilirse doğrudan açar.
    """
    img = None
    # Path'i normalize et (Windows için)
    url = os.path.normpath(url)

    if os.path.isfile(url):
        img = Image.open(url).convert("RGBA")
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; VirtualTryOn/1.0; +https://example.com)"
        }
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                break
            except Exception as e:
                last_exc = e
        if img is None:
            raise RuntimeError(f"Resim indirilemedi: {url}\nHata: {last_exc}")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path)

    return img
