import os
import firebase_admin
from firebase_admin import credentials, firestore, storage

from .config import SERVICE_ACCOUNT_PATH, FIREBASE_STORAGE_BUCKET

if not os.path.isfile(SERVICE_ACCOUNT_PATH):
    raise RuntimeError(
        "serviceAccountKey.json bulunamadı. Firebase Admin SDK için bu dosyayı "
        "proje köküne koyun. Dosya GitHub'a yüklenmemelidir."
    )

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})

db = firestore.client()
bucket = storage.bucket()

__all__ = ["db", "bucket"]
