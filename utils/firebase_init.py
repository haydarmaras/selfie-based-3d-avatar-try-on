# utils/firebase_init.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Proje kökü: .../bitirme_projesi
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVICE_ACCOUNT_PATH = os.path.join(PROJECT_ROOT, "serviceAccountKey.json")
FIREBASE_STORAGE_BUCKET = "bitirmeprojesi-9b244.firebasestorage.app"  # kendi bucket adın

# Firebase başlat
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_STORAGE_BUCKET,
    })

# Firestore ve Storage client’ları
db = firestore.client()
bucket = storage.bucket()

__all__ = ["db", "bucket", "PROJECT_ROOT"]
