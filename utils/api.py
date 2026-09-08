import os
import traceback

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .avatar_generator import generate_avatar_for_user, validate_measurements
from .config import AVATAR_DIR, CLOTHES_DIR
from .firebase_init import bucket, db

app = FastAPI(title="Selfie 3D Avatar API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_IMAGE_BYTES = 15 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _check_user_id(user_id: str):
    if not user_id or len(user_id) > 128 or "/" in user_id or "\\" in user_id:
        raise HTTPException(status_code=400, detail="Geçersiz user_id")


def _validate_upload(file: UploadFile):
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Sadece JPG, PNG veya WEBP yükleyebilirsiniz.")


async def _save_upload(file: UploadFile, path: str):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail=f"Boş dosya: {file.filename}")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Görsel 15 MB'dan küçük olmalıdır.")
    with open(path, "wb") as f:
        f.write(data)
    return data


@app.get("/health")
def health():
    return {"status": "ok", "service": "avatar-api", "version": "3.0"}


@app.post("/avatar_olustur")
async def avatar_olustur(
    user_id: str = Form(...),
    selfie_front: UploadFile = File(...),
    selfie_side: UploadFile = File(...),
    boy: float = Form(...),
    kilo: float = Form(...),
    cinsiyet: str = Form(...),
    omuz_genisligi: float = Form(...),
    bel_cevresi: float = Form(...),
    kalca_cevresi: float = Form(...),
    bacak_uzunlugu: float = Form(...),
):
    _check_user_id(user_id)
    _validate_upload(selfie_front)
    _validate_upload(selfie_side)

    try:
        measurements = validate_measurements({
            "boy": boy,
            "kilo": kilo,
            "omuz_genisligi": omuz_genisligi,
            "bel_cevresi": bel_cevresi,
            "kalca_cevresi": kalca_cevresi,
            "bacak_uzunlugu": bacak_uzunlugu,
        })

        os.makedirs(AVATAR_DIR, exist_ok=True)
        front_path = os.path.join(AVATAR_DIR, f"{user_id}_front.jpg")
        side_path = os.path.join(AVATAR_DIR, f"{user_id}_side.jpg")
        front_data = await _save_upload(selfie_front, front_path)
        side_data = await _save_upload(selfie_side, side_path)

        bucket.blob(f"selfies/{user_id}_front.jpg").upload_from_string(
            front_data, content_type=selfie_front.content_type or "image/jpeg"
        )
        bucket.blob(f"selfies/{user_id}_side.jpg").upload_from_string(
            side_data, content_type=selfie_side.content_type or "image/jpeg"
        )

        db.collection("users").document(user_id).set({
            **measurements,
            "cinsiyet": cinsiyet,
            "selfie_front": f"selfies/{user_id}_front.jpg",
            "selfie_side": f"selfies/{user_id}_side.jpg",
            "avatar_status": "queued",
        }, merge=True)

        avatar_url = generate_avatar_for_user(user_id)
        return {"status": "ok", "avatar_url": avatar_url}

    except HTTPException:
        raise
    except Exception as exc:
        print("\nAVATAR API HATASI:", exc)
        print(traceback.format_exc())
        db.collection("users").document(user_id).set(
            {"avatar_status": "error", "avatar_error": str(exc)[:1000]}, merge=True
        )
        return {"status": "error", "message": str(exc)}


@app.post("/kiyafet_ekle")
async def kiyafet_ekle(
    user_id: str = Form(...),
    clothing_image: UploadFile = File(...),
):
    _check_user_id(user_id)
    _validate_upload(clothing_image)

    try:
        user_ref = db.collection("users").document(user_id)
        if not user_ref.get().exists:
            raise HTTPException(status_code=404, detail="Kullanıcı profili bulunamadı.")

        os.makedirs(CLOTHES_DIR, exist_ok=True)
        cloth_path = os.path.join(CLOTHES_DIR, f"{user_id}.jpg")
        data = await _save_upload(clothing_image, cloth_path)

        blob = bucket.blob(f"clothes/{user_id}.jpg")
        blob.upload_from_string(data, content_type=clothing_image.content_type or "image/jpeg")

        user_ref.set({
            "has_clothing": True,
            "clothing_storage_path": f"clothes/{user_id}.jpg",
            "avatar_status": "queued",
        }, merge=True)

        avatar_url = generate_avatar_for_user(user_id)
        return {"status": "ok", "avatar_url": avatar_url}

    except HTTPException:
        raise
    except Exception as exc:
        print("\nKIYAFET API HATASI:", exc)
        print(traceback.format_exc())
        return {"status": "error", "message": str(exc)}
