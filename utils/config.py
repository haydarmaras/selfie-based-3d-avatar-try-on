import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AVATAR_DIR = os.path.join(PROJECT_ROOT, "avatar")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
CLOTHES_DIR = os.path.join(PROJECT_ROOT, "clothes")
BLENDER_INTEGRATION_DIR = os.path.join(PROJECT_ROOT, "utils", "blender_integration")
BLENDER_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "blender_scripts")
BASE_MODELS_DIR = os.path.join(PROJECT_ROOT, "base_models")
HAIR_MODELS_DIR = os.path.join(PROJECT_ROOT, "hair_models")
SERVICE_ACCOUNT_PATH = os.path.join(PROJECT_ROOT, "serviceAccountKey.json")

FIREBASE_STORAGE_BUCKET = os.getenv(
    "FIREBASE_STORAGE_BUCKET", "bitirmeprojesi-9b244.firebasestorage.app"
)
BLENDER_EXE = os.getenv("BLENDER_EXE", "")

for path in (AVATAR_DIR, OUTPUT_DIR, CLOTHES_DIR, BLENDER_INTEGRATION_DIR):
    os.makedirs(path, exist_ok=True)


def find_blender_executable() -> str:
    candidates = []
    if BLENDER_EXE:
        candidates.append(BLENDER_EXE)

    candidates.extend([
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    ])

    which = shutil.which("blender")
    if which:
        candidates.append(which)

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    raise RuntimeError(
        "Blender bulunamadı. Blender'ı kurun veya BLENDER_EXE ortam değişkenini "
        "blender.exe'nin tam yoluna ayarlayın."
    )


def base_model_path(gender: str) -> str:
    normalized = str(gender).strip().lower()
    filename = "male.glb" if normalized in {"erkek", "male", "m", "man"} else "female.glb"
    return os.path.join(BASE_MODELS_DIR, filename)


def hair_model_path(gender: str, preset: str | None = None) -> str | None:
    if preset:
        path = os.path.join(HAIR_MODELS_DIR, os.path.basename(preset))
        if os.path.isfile(path):
            return path

    defaults = (
        "male_short_middle_part.glb"
        if str(gender).strip().lower() in {"erkek", "male", "m", "man"}
        else "female_default.glb"
    )
    path = os.path.join(HAIR_MODELS_DIR, defaults)
    return path if os.path.isfile(path) else None
