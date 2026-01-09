from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback

from .avatar_generator import generate_avatar_for_user
from .firebase_init import db, bucket

app = FastAPI(title="Avatar API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    try:
        print("\nAPI çağrıldı — /avatar_olustur")
        print("Kullanıcı:", user_id)

        os.makedirs("avatar", exist_ok=True)

        front_path = os.path.join("avatar", f"{user_id}_front.jpg")
        with open(front_path, "wb") as f:
            f.write(await selfie_front.read())
        print("Ön selfie kaydedildi:", front_path)

        front_blob = bucket.blob(f"selfies/{user_id}_front.jpg")
        front_blob.upload_from_filename(front_path, content_type="image/jpeg")

        side_path = os.path.join("avatar", f"{user_id}_side.jpg")
        with open(side_path, "wb") as f:
            f.write(await selfie_side.read())
        print("Yan selfie kaydedildi:", side_path)

        side_blob = bucket.blob(f"selfies/{user_id}_side.jpg")
        side_blob.upload_from_filename(side_path, content_type="image/jpeg")

        db.collection("users").document(user_id).set(
            {
                "boy": boy,
                "kilo": kilo,
                "cinsiyet": cinsiyet,
                "omuz_genisligi": omuz_genisligi,
                "bel_cevresi": bel_cevresi,
                "kalca_cevresi": kalca_cevresi,
                "bacak_uzunlugu": bacak_uzunlugu,
                "selfie_front": f"selfies/{user_id}_front.jpg",
                "selfie_side": f"selfies/{user_id}_side.jpg",
            },
            merge=True,
        )

        avatar_url = generate_avatar_for_user(user_id)
        if not avatar_url:
            return {"status": "error", "message": "Avatar üretimi başarısız."}

        return {"status": "ok", "avatar_url": avatar_url}

    except Exception as e:
        print("\nAPI HATASI:", e)
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.post("/kiyafet_ekle")
async def kiyafet_ekle(
    user_id: str = Form(...),
    clothing_image: UploadFile = File(...),
):
    try:
        print("\nAPI çağrıldı — /kiyafet_ekle")
        print("Kullanıcı:", user_id)

        os.makedirs("clothes", exist_ok=True)

        cloth_path = os.path.join("clothes", f"{user_id}.jpg")
        with open(cloth_path, "wb") as f:
            f.write(await clothing_image.read())

        # firestore'a "local path" yazmak yerine sadece "var" demek yeter
        db.collection("users").document(user_id).set(
            {"has_clothing": True},
            merge=True,
        )

        # avatarı yeniden üret (build_avatar.py kıyafeti görüp uygular)
        avatar_url = generate_avatar_for_user(user_id)

        return {"status": "ok", "avatar_url": avatar_url}

    except Exception as e:
        print("\nKIYAFET API HATASI:", e)
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}
