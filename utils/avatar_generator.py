import os
import json
import subprocess
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from .firebase_init import db, bucket

UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_AVATAR_DIR = os.path.join(UTILS_DIR, "avatars")
LOCAL_OUTPUT_DIR = os.path.join(UTILS_DIR, "outputs")
BLENDER_INTEGRATION_DIR = os.path.join(UTILS_DIR, "blender_integration")

PROJECT_ROOT = os.path.dirname(UTILS_DIR)
BASE_MODELS_DIR = os.path.join(PROJECT_ROOT, "base_models")
BLENDER_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "blender_scripts")

CONFIG_PATH_TEMPLATE = os.path.join(BLENDER_INTEGRATION_DIR, "{}_config.json")

os.makedirs(LOCAL_AVATAR_DIR, exist_ok=True)
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
os.makedirs(BLENDER_INTEGRATION_DIR, exist_ok=True)

BLENDER_EXE = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
BLENDER_SCRIPT_PATH = os.path.join(BLENDER_SCRIPTS_DIR, "build_avatar.py")


def extract_hair_mask(path: str):
    mp_seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    img = cv2.imread(path)
    if img is None:
        return None
    seg = mp_seg.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).segmentation_mask
    seg = (seg * 255).astype("uint8")
    hair_mask = (seg > 180).astype("uint8") * 255
    return hair_mask


def estimate_colors(path: str, hair_mask):
    fallback_skin = np.array([220, 190, 170], dtype=np.float32)
    fallback_hair = np.array([60, 40, 30], dtype=np.float32)
    fallback_eye = np.array([80, 80, 80], dtype=np.float32)

    img_bgr = cv2.imread(path)
    if img_bgr is None:
        return fallback_skin, fallback_hair, fallback_eye

    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape

    # skin
    sx1, sx2 = int(w * 0.30), int(w * 0.70)
    sy1, sy2 = int(h * 0.30), int(h * 0.70)
    face_crop = img[sy1:sy2, sx1:sx2]
    skin = face_crop.reshape(-1, 3).mean(axis=0) if face_crop.size > 0 else fallback_skin

    # hair
    if hair_mask is not None:
        hair_mask = cv2.resize(hair_mask, (w, h))
        pixels = img[hair_mask > 0]
        hair = pixels.reshape(-1, 3).mean(axis=0) if pixels.size > 0 else fallback_hair
    else:
        hair = fallback_hair

    # eye (basit)
    ex1, ex2 = int(w * 0.35), int(w * 0.65)
    ey1, ey2 = int(h * 0.35), int(h * 0.50)
    eye_crop = img[ey1:ey2, ex1:ex2]
    eye = eye_crop.reshape(-1, 3).mean(axis=0) if eye_crop.size > 0 else fallback_eye

    return skin, hair, eye


def pick_base_model_path(gender: str) -> str:
    g = str(gender).lower()
    if g in ["erkek", "male", "m"]:
        return os.path.join(BASE_MODELS_DIR, "male.glb")
    return os.path.join(BASE_MODELS_DIR, "female.glb")


def run_blender_for_user(user_id: str):
    cmd = [
        BLENDER_EXE,
        "-b",
        "--python",
        BLENDER_SCRIPT_PATH,
        "--",
        user_id,
    ]
    print("[BLENDER CMD]", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Blender hata returncode={res.returncode}")


def generate_avatar_for_user(user_id: str) -> Optional[str]:
    print(f"\n=== Avatar Üretimi Başladı: {user_id} ===")

    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise RuntimeError("users/<uid> yok")

    user = user_doc.to_dict() or {}
    gender = user.get("cinsiyet", "erkek")

    # selfie'yi storage'dan indir
    selfie_local = os.path.join(LOCAL_AVATAR_DIR, f"{user_id}_front.jpg")
    front_blob = bucket.blob(f"selfies/{user_id}_front.jpg")
    if not front_blob.exists():
        raise RuntimeError("Ön selfie storage'da yok")
    front_blob.download_to_filename(selfie_local)

    # renkler
    mask = extract_hair_mask(selfie_local)
    skin, hair, eye = estimate_colors(selfie_local, mask)

    base_model_path = pick_base_model_path(gender)
    if not os.path.exists(base_model_path):
        raise RuntimeError(f"Base model yok: {base_model_path}")

    output_glb = os.path.join(LOCAL_OUTPUT_DIR, f"{user_id}.glb")

    # hair preset seçimi (firestore'dan)
    hair_preset = user.get("hair_preset")
    if not hair_preset:
        hair_preset = "male_short_middle_part.glb" if str(gender).lower() in ["erkek", "male", "m"] else "female_default.glb"

    cfg = {
        "user_id": user_id,
        "base_model_path": base_model_path,
        "output_glb_path": output_glb,
        "colors": {
            "skin": skin.tolist(),
            "hair": hair.tolist(),
            "eye": eye.tolist(),
        },
        "hair_preset": hair_preset,
        # Kıyafet: build_avatar.py local'den okuyacak
        "clothing_local_path": os.path.join(PROJECT_ROOT, "clothes", f"{user_id}.jpg"),
    }

    cfg_path = CONFIG_PATH_TEMPLATE.format(user_id)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    run_blender_for_user(user_id)

    if not os.path.exists(output_glb):
        raise RuntimeError("Blender GLB üretmedi")

    blob_out = bucket.blob(f"avatars/{user_id}.glb")
    blob_out.upload_from_filename(output_glb, content_type="model/gltf-binary")
    blob_out.make_public()

    url = blob_out.public_url
    user_ref.set({"avatar_url": url}, merge=True)

    print("=== Avatar Üretimi TAMAMLANDI ===")
    print("Avatar URL:", url)
    return url
