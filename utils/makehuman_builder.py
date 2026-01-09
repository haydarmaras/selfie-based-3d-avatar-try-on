import os

BASE_DIR = r"C:\okul\bitirme_projesi\base_models"
TEMPLATE_MHM = os.path.join(BASE_DIR, "default_avatar.mhm")

def generate_mhm(user_id, gender, height, weight, chest, waist, hips, leg):
    out_path = os.path.join(BASE_DIR, f"{user_id}.mhm")

    # normalize helpers (0.0–1.0 arası slider dönüşümü)
    def norm(val, min_v, max_v):
        return max(0.0, min(1.0, (val - min_v) / (max_v - min_v)))

    # MakeHuman slider eşleştirmeleri
    params = {
        "macrodetails-universal-height": norm(height, 150, 200),   # boy
        "macrodetails-universal-weight": norm(weight, 45, 120),    # kilo
        "measure-chest-circumference": chest / 150.0,              # göğüs
        "measure-waist-circumference": waist / 120.0,              # bel
        "measure-hips-circumference": hips / 150.0,                # kalça
        "macrodetails-universal-legsize": leg / 150.0,             # bacak uzunluğu
        "gender": 1.0 if gender.lower() in ["erkek", "male"] else 0.0
    }

    # default mhm dosyasını oku
    with open(TEMPLATE_MHM, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2:
            key, value = parts
            if key in params:
                new_lines.append(f"{key} {params[key]:.3f}\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(out_path, "w") as f:
        f.writelines(new_lines)

    return out_path
