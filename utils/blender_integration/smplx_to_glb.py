import os
import torch
import trimesh
from smplx import SMPLX


# =====================================================================
# SMPL-X MODEL YÜKLEME
# =====================================================================
def load_smplx_model(model_dir, gender="male", num_betas=10, num_expression_coeffs=10):
    gender = gender.lower()
    if gender not in ["male", "female", "neutral"]:
        gender = "neutral"

    model_path = os.path.join(model_dir, gender)

    if not os.path.exists(model_path):
        raise RuntimeError(f"SMPL-X model klasörü bulunamadı: {model_path}")

    print(f"[SMPLX] Model yükleniyor → {model_path}")

    model = SMPLX(
        model_path,
        gender=gender,
        num_betas=num_betas,
        num_expression_coeffs=num_expression_coeffs,
        flat_hand_mean=True,
        use_pca=False
    )
    return model


# =====================================================================
# KULLANICI ÖLÇÜLERİNİ BETALARA MAPLE
# =====================================================================
def normalize_shape(chest, waist, hip):
    betas = torch.zeros(10)

    betas[0] = (chest - 92) / 50
    betas[1] = (waist - 80) / 40
    betas[2] = (hip - 95) / 45

    return betas


# =====================================================================
# DOĞRUDAN GLB OLUŞTURMA (BLENDER YOK!)
# =====================================================================
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
):
    """
    SMPL-X mesh üretir → GLB olarak kaydeder.
    """

    # 1) Modeli yükle
    model = load_smplx_model(model_dir, gender)

    # 2) Beta & Expression
    betas = normalize_shape(chest, waist, hip)
    expressions = torch.zeros(10)

    with torch.no_grad():
        model.betas.copy_(betas)
        model.expression.copy_(expressions)

    # 3) Mesh oluştur
    print("[SMPLX] Mesh oluşturuluyor...")
    output = model()
    vertices = output.vertices[0].detach().cpu().numpy()
    faces = model.faces

    # 4) Boy scaling
    scale = float(height) / 166.0    # SMPL-X varsayılan boy: 1.66m
    vertices *= scale

    # 5) GLB export
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
    mesh.export(output_glb_path)

    print("[SMPLX] GLB yazıldı →", output_glb_path)
    return output_glb_path
