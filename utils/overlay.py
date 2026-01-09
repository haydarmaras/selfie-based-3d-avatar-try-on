import argparse
import os
from PIL import Image


def run_pipeline(cloth_path, avatar_path, out_path):
    print("1) Kıyafet yükleniyor...")
    cloth_img = Image.open(cloth_path).convert("RGBA")

    print("2) Avatar yükleniyor...")
    avatar_img = Image.open(avatar_path).convert("RGBA")

    print("3) Görüntü birleştiriliyor...")
    cloth_img_resized = cloth_img.resize(avatar_img.size)
    result_img = Image.alpha_composite(avatar_img, cloth_img_resized)

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        result_img.save(out_path)
        print(f"4) Sonuç kaydedildi: {out_path}")
    else:
        result_img.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Virtual Try-On Script")
    parser.add_argument("--cloth_url", required=True, help="Kıyafet dosya yolu (yerel)")
    parser.add_argument("--avatar", required=True, help="Avatar dosya yolu")
    parser.add_argument("--out", help="Kaydedilecek çıktı yolu")
    args = parser.parse_args()

    run_pipeline(args.cloth_url, args.avatar, args.out)
