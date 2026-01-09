# utils/smplx_builder.py

import os
import cv2
import torch
import numpy as np
import trimesh
from smplx import SMPLX


# ============================================================
#  SMPL-X MODEL YÜKLEME
# ============================================================
def load_smplx_model(model_dir, gender="male", num_betas=10, num_expression_coeffs=10):
    """
    Cinsiyete göre SMPL-X modeli yükler.
    Klasör yapın:
        smplx_models/
            male/
            female/
            neutral/
    """
    g_raw = str(gender).lower()

    if g_raw in ["erkek", "e", "male", "man", "m"]:
        gender = "male"
    elif g_raw in ["kadın", "kadin", "bayan", "f", "female", "woman"]:
        gender = "female"
    else:
        gender = "neutral"

    model_path = os.path.join(model_dir, gender)

    if not os.path.exists(model_path):
        raise RuntimeError(f"SMPL-X model klasörü bulunamadı: {model_path}")

    print(f"[SMPLX] Model Yükleniyor → {model_path} (gender={gender})")

    model = SMPLX(
        model_path,
        gender=gender,
        num_betas=num_betas,
        num_expression_coeffs=num_expression_coeffs,
        flat_hand_mean=True,
        use_pca=False,
    )

    return model


# ============================================================
#  VÜCUT ÖLÇÜLERİNİ BETA'YA MAP ETME
# ============================================================
def normalize_shape(chest, waist, hip, height, weight, leg_length):
    """
    Kullanıcı ölçülerini SMPL-X shape betalarına çevir.
    Biraz abartılı mapping → fark bariz olsun.
    """
    betas = torch.zeros(10)

    # Ortalama referans değerler
    ref_chest = 96.0
    ref_waist = 82.0
    ref_hip = 98.0
    ref_height = 175.0
    ref_weight = 75.0
    ref_leg = 95.0

    betas[0] = (chest - ref_chest) / 4.0    # göğüs
    betas[1] = (waist - ref_waist) / 4.0    # bel
    betas[2] = (hip - ref_hip) / 4.0        # kalça
    betas[3] = (height - ref_height) / 8.0  # boy
    betas[4] = (weight - ref_weight) / 6.0  # kilo
    betas[5] = (leg_length - ref_leg) / 4.0 # bacak uzunluğu

    # Biraz rastgele varyasyon (daha organik görünmesi için çok hafif)
    betas[7] = (waist - ref_waist) / 12.0
    betas[8] = (chest - ref_chest) / 12.0

    print("[SMPLX] Hesaplanan Betalar:", betas)

    return betas


# ============================================================
#  SELFIE'DEN RENK ALMA
# ============================================================
def estimate_colors_from_selfie(selfie_path: str, hair_mask_path: str | None):
    """
    Selfie'den saç rengi + cilt rengi tahmin et.
    """
    # Varsayılan renkler (fallback)
    skin_color = np.array([233, 205, 187, 255], dtype=np.uint8)
    hair_color = np.array([60, 40, 30, 255], dtype=np.uint8)

    if not selfie_path or not os.path.exists(selfie_path):
        return skin_color, hair_color

    img_bgr = cv2.imread(selfie_path)
    if img_bgr is None:
        return skin_color, hair_color

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = img_rgb.shape

    # Yüz bölgesi tahmini (gövde yok, sadece yüz ortası)
    x1 = int(w * 0.3)
    x2 = int(w * 0.7)
    y1 = int(h * 0.25)
    y2 = int(h * 0.75)
    face_crop = img_rgb[y1:y2, x1:x2]

    if face_crop.size > 0:
        skin_mean = face_crop.reshape(-1, 3).mean(axis=0)
        skin_color = np.array([skin_mean[0], skin_mean[1], skin_mean[2], 255], dtype=np.uint8)

    # Saç rengi – maskeden
    if hair_mask_path and os.path.exists(hair_mask_path):
        mask = cv2.imread(hair_mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is not None:
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
            hair_pixels = img_rgb[mask > 128]
            if hair_pixels.size > 0:
                hair_mean = hair_pixels.reshape(-1, 3).mean(axis=0)
                hair_color = np.array([hair_mean[0], hair_mean[1], hair_mean[2], 255], dtype=np.uint8)

    return skin_color, hair_color


# ============================================================
#  DOĞRUDAN GLB OLUŞTURMA (BLENDER YOK)
# ============================================================
def build_smplx_mesh_glb(
    model_dir,
    output_glb_path,
    gender,
    height,
    weight,
    chest,
    waist,
    hip,
    leg_length,
    selfie_path=None,
    hair_mask_path=None,
):
    """
    SMPL-X mesh üretir → DOĞRUDAN GLB olarak kaydeder.
    """
    # 1) Modeli yükle
    model = load_smplx_model(model_dir, gender)

    # 2) Shape parametreleri
    betas = normalize_shape(chest, waist, hip, height, weight, leg_length)
    expressions = torch.zeros(10)

    with torch.no_grad():
        model.betas.copy_(betas)
        model.expression.copy_(expressions)

    # 3) Mesh oluştur
    print("[SMPLX] Mesh oluşturuluyor...")
    output = model()
    vertices = output.vertices[0].detach().cpu().numpy()
    faces = model.faces

    # 4) Boy scaling (SMPL-X default ~1.66m)
    base_height_m = 1.66
    scale_factor = float(height) / (base_height_m * 100.0)  # cm → m
    vertices *= scale_factor
    print(f"[SMPLX] Boy scale factor: {scale_factor:.3f}")

    # 5) Selfie'den renkleri al
    skin_color, hair_color = estimate_colors_from_selfie(selfie_path, hair_mask_path)

    num_verts = vertices.shape[0]
    colors = np.tile(skin_color, (num_verts, 1))

    # Baş bölgesi: üst %20'lik kısım → saç rengi
    y_vals = vertices[:, 1]
    y_min, y_max = y_vals.min(), y_vals.max()
    head_start = y_max - 0.20 * (y_max - y_min)
    colors[y_vals > head_start] = hair_color

    # 6) Trimesh → GLB export (vertex_colors ile)
    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces,
        vertex_colors=colors,
        process=False,
    )
    mesh.export(output_glb_path)
    print("[SMPLX] GLB yazıldı →", output_glb_path)

    return output_glb_path
