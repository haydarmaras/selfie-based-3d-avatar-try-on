import json
import os
import subprocess
import uuid
from datetime import timedelta
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from .config import (
    AVATAR_DIR,
    BLENDER_INTEGRATION_DIR,
    BLENDER_SCRIPTS_DIR,
    CLOTHES_DIR,
    OUTPUT_DIR,
    base_model_path,
    find_blender_executable,
    hair_model_path,
)
from .firebase_init import bucket, db

BLENDER_SCRIPT_PATH = os.path.join(BLENDER_SCRIPTS_DIR, "build_avatar.py")
CONFIG_PATH_TEMPLATE = os.path.join(BLENDER_INTEGRATION_DIR, "{}_config.json")


def _safe_float(value, name, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} sayısal olmalıdır.")
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} {minimum:g}-{maximum:g} aralığında olmalıdır.")
    return number


def validate_measurements(data):
    return {
        "boy": _safe_float(data.get("boy"), "Boy", 100, 250),
        "kilo": _safe_float(data.get("kilo"), "Kilo", 25, 300),
        "omuz_genisligi": _safe_float(data.get("omuz_genisligi"), "Omuz", 20, 100),
        "bel_cevresi": _safe_float(data.get("bel_cevresi"), "Bel", 40, 180),
        "kalca_cevresi": _safe_float(data.get("kalca_cevresi"), "Kalça", 40, 200),
        "bacak_uzunlugu": _safe_float(data.get("bacak_uzunlugu"), "Bacak uzunluğu", 40, 160),
    }


def extract_face_data(path: str):
    img = cv2.imread(path)
    if img is None:
        raise RuntimeError(f"Görüntü okunamadı: {path}")

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as face_mesh:
        result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        return []

    return [
        {"x": round(float(p.x), 6), "y": round(float(p.y), 6), "z": round(float(p.z), 6)}
        for p in result.multi_face_landmarks[0].landmark
    ]


def extract_hair_mask(path: str):
    img = cv2.imread(path)
    if img is None:
        return None

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1) as seg_model:
        mask = seg_model.process(rgb).segmentation_mask

    # SelfieSegmentation insan maskesi verir; saç segmentasyonu değildir.
    # Bu yüzden yüzün üstündeki kişi maskesini saç için yaklaşık bölge olarak kullanıyoruz.
    person = (mask > 0.65).astype(np.uint8) * 255
    upper = np.zeros_like(person)
    upper[: int(h * 0.42), :] = person[: int(h * 0.42), :]
    upper[:, : int(w * 0.12)] = 0
    upper[:, int(w * 0.88) :] = 0
    return cv2.morphologyEx(upper, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))


def _robust_mean(pixels, fallback):
    if pixels is None or pixels.size == 0:
        return np.asarray(fallback, dtype=np.float32)
    values = pixels.reshape(-1, 3).astype(np.float32)
    # Aşırı parlak/karanlık pikselleri at.
    brightness = values.mean(axis=1)
    values = values[(brightness > 20) & (brightness < 245)]
    if len(values) == 0:
        return np.asarray(fallback, dtype=np.float32)
    return np.median(values, axis=0)


def estimate_colors(path: str, hair_mask):
    fallback_skin = np.array([220, 190, 170], dtype=np.float32)
    fallback_hair = np.array([60, 40, 30], dtype=np.float32)
    fallback_eye = np.array([80, 80, 80], dtype=np.float32)

    img_bgr = cv2.imread(path)
    if img_bgr is None:
        return fallback_skin, fallback_hair, fallback_eye
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]

    face = img[int(h * 0.25):int(h * 0.65), int(w * 0.30):int(w * 0.70)]
    skin = _robust_mean(face, fallback_skin)

    if hair_mask is not None:
        hm = cv2.resize(hair_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        hair = _robust_mean(img[hm > 0], fallback_hair)
    else:
        hair = fallback_hair

    eye = _robust_mean(img[int(h * 0.35):int(h * 0.50), int(w * 0.35):int(w * 0.65)], fallback_eye)
    return skin, hair, eye


def _download_selfie(user_id: str, suffix: str):
    local = os.path.join(AVATAR_DIR, f"{user_id}_{suffix}.jpg")
    blob = bucket.blob(f"selfies/{user_id}_{suffix}.jpg")
    if not blob.exists():
        raise RuntimeError(f"Firebase Storage'da {suffix} selfie bulunamadı.")
    blob.download_to_filename(local)
    return local


def _download_clothing_if_needed(user_id: str):
    local = os.path.join(CLOTHES_DIR, f"{user_id}.jpg")
    if os.path.isfile(local):
        return local
    blob = bucket.blob(f"clothes/{user_id}.jpg")
    if blob.exists():
        blob.download_to_filename(local)
        return local
    return None


def _publish_file(blob_path: str, local_path: str, content_type: str) -> str:
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    token = str(uuid.uuid4())
    blob.metadata = {**(blob.metadata or {}), "firebaseStorageDownloadTokens": token}
    blob.patch()
    encoded = blob.name.replace("/", "%2F")
    return (
        "https://firebasestorage.googleapis.com/v0/b/"
        f"{bucket.name}/o/{encoded}?alt=media&token={token}"
    )


def run_blender_for_user(user_id: str):
    blender = find_blender_executable()
    if not os.path.isfile(BLENDER_SCRIPT_PATH):
        raise RuntimeError(f"Blender script bulunamadı: {BLENDER_SCRIPT_PATH}")
    cmd = [blender, "-b", "--python", BLENDER_SCRIPT_PATH, "--", user_id]
    print("[BLENDER CMD]", subprocess.list2cmdline(cmd))
    result = subprocess.run(cmd, cwd=os.path.dirname(BLENDER_SCRIPT_PATH), text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Blender hata verdi. returncode={result.returncode}")


def generate_avatar_for_user(user_id: str) -> Optional[str]:
    user_ref = db.collection("users").document(user_id)
    snapshot = user_ref.get()
    if not snapshot.exists:
        raise RuntimeError("users/<uid> Firestore belgesi yok.")

    user = snapshot.to_dict() or {}
    measurements = validate_measurements(user)
    gender = user.get("cinsiyet", "Erkek")

    front_path = _download_selfie(user_id, "front")
    side_path = _download_selfie(user_id, "side")

    face_front = extract_face_data(front_path)
    face_side = extract_face_data(side_path)
    if not face_front:
        raise RuntimeError("Ön selfie'de yüz bulunamadı. Yüzün net göründüğü bir fotoğraf yükleyin.")

    hair_mask = extract_hair_mask(front_path)
    skin, hair, eye = estimate_colors(front_path, hair_mask)

    base_path = base_model_path(gender)
    if not os.path.isfile(base_path):
        raise RuntimeError(
            f"Base model bulunamadı: {base_path}. "
            "base_models/male.glb ve female.glb dosyalarını yerel projeye ekleyin."
        )

    hair_preset = user.get("hair_preset")
    hair_path = hair_model_path(gender, hair_preset)

    clothing_path = _download_clothing_if_needed(user_id)
    output_path = os.path.join(OUTPUT_DIR, f"{user_id}.glb")

    cfg = {
        "user_id": user_id,
        "base_model_path": base_path,
        "output_glb_path": output_path,
        "measurements": measurements,
        "colors": {
            "skin": skin.tolist(),
            "hair": hair.tolist(),
            "eye": eye.tolist(),
        },
        "hair_model_path": hair_path or "",
        "clothing_local_path": clothing_path or "",
        "face_landmarks": {"front": face_front, "side": face_side},
    }

    cfg_path = CONFIG_PATH_TEMPLATE.format(user_id)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    user_ref.set({
        "face_landmarks_count": len(face_front),
        "avatar_status": "generating",
    }, merge=True)

    run_blender_for_user(user_id)
    if not os.path.isfile(output_path) or os.path.getsize(output_path) < 1024:
        raise RuntimeError("Blender geçerli bir GLB üretmedi.")

    url = _publish_file(f"avatars/{user_id}.glb", output_path, "model/gltf-binary")
    user_ref.set({"avatar_url": url, "avatar_status": "ready"}, merge=True)
    return url
