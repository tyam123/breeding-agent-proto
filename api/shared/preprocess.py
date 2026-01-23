# /api/shared/preprocess.py
from io import BytesIO
from PIL import Image, ImageOps

def preprocess_image_bytes(
    img_bytes: bytes,
    orientation_policy: str = "force_portrait",
    max_side: int = 1024,
    jpeg_quality: int = 85,
) -> bytes:
    # EXIFの向き補正（ただし最終は policy が勝つ）
    img = Image.open(BytesIO(img_bytes))
    img = ImageOps.exif_transpose(img)

    w, h = img.size

    # ここがあなたの合意：デフォは縦固定
    if orientation_policy == "force_portrait":
        if w > h:
            img = img.rotate(90, expand=True)
    elif orientation_policy == "force_landscape":
        if h > w:
            img = img.rotate(90, expand=True)
    elif orientation_policy == "exif_auto":
        pass
    else:
        # 未知のポリシーは安全側：縦固定
        if w > h:
            img = img.rotate(90, expand=True)

    # リサイズ（最大辺）
    w, h = img.size
    scale = max(w, h) / float(max_side)
    if scale > 1.0:
        img = img.resize((int(w / scale), int(h / scale)))

    # JPEG化（コスト削減）
    out = BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=int(jpeg_quality), optimize=True)
    return out.getvalue()
