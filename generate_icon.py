"""Generate PayPack icon – blue background + paypack text. Clean and simple."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT_DIR, exist_ok=True)
S = 256

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# ── Blue rounded background ──
d.rounded_rectangle((0, 0, S, S), radius=48, fill=(24, 100, 210, 255))

# ── "paypack" text in white ──
try:
    font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 52)
except Exception:
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
    except Exception:
        font = ImageFont.load_default()

text = "paypack"
bbox = d.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((S - tw) // 2, (S - th) // 2), text, fill=(255, 255, 255, 255), font=font)

# ── Save ──
for size, name in [(256, "paypack_icon"), (128, "paypack_icon_128"), (64, "paypack_icon_64")]:
    resized = img.resize((size, size), Image.LANCZOS) if size != S else img
    path = os.path.join(OUT_DIR, f"{name}.png")
    resized.save(path, "PNG")
    print(f"  {path}  ({size}x{size})")
print("\nDone.")
