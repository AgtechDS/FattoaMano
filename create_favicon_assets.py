import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_DIR = Path(__file__).resolve().parent
assets_dir = WORKSPACE_DIR / "assets"
assets_dir.mkdir(exist_ok=True)

# Crea un canvas 256x256 con sfondo Dark Obsidian ed emblema Rame Puro
def create_copper_icon(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base squircle
    pad = int(size * 0.05)
    radius = int(size * 0.22)
    # Bordo esterno rame
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=radius,
        fill=(18, 18, 24, 255),
        outline=(200, 125, 85, 255),
        width=int(size * 0.035)
    )

    # Anello interno dorato/rame
    inner_pad = int(size * 0.1)
    draw.rounded_rectangle(
        [(inner_pad, inner_pad), (size - inner_pad, size - inner_pad)],
        radius=int(radius * 0.8),
        fill=(10, 10, 14, 255),
        outline=(217, 130, 76, 120),
        width=int(size * 0.015)
    )

    # Lettera F e M stilizzate
    # Disegniamo barre geometriche eleganti
    copper_color = (217, 130, 76, 255)
    copper_light = (230, 152, 112, 255)

    # F
    fx = int(size * 0.28)
    fy = int(size * 0.28)
    fw = int(size * 0.08)
    fh = int(size * 0.44)
    # Asta verticale F
    draw.rectangle([(fx, fy), (fx + fw, fy + fh)], fill=copper_color)
    # Traversa superiore F
    draw.rectangle([(fx, fy), (fx + int(size * 0.22), fy + int(size * 0.07))], fill=copper_light)
    # Traversa centrale F
    draw.rectangle([(fx, fy + int(size * 0.16)), (fx + int(size * 0.18), fy + int(size * 0.23))], fill=copper_color)

    # M
    mx = int(size * 0.52)
    my = int(size * 0.28)
    mw = int(size * 0.08)
    mh = int(size * 0.44)
    # Asta sx M
    draw.rectangle([(mx, my), (mx + mw, my + mh)], fill=copper_color)
    # Asta dx M
    draw.rectangle([(mx + int(size * 0.20), my), (mx + int(size * 0.20) + mw, my + mh)], fill=copper_color)
    # Diagonali M
    draw.polygon([
        (mx + mw, my),
        (mx + int(size * 0.14), my + int(size * 0.20)),
        (mx + int(size * 0.10), my + int(size * 0.20))
    ], fill=copper_light)
    draw.polygon([
        (mx + int(size * 0.20), my),
        (mx + int(size * 0.14), my + int(size * 0.20)),
        (mx + int(size * 0.18), my + int(size * 0.20))
    ], fill=copper_light)

    # Scintilla / Punto di fuoco in rame fuso
    spark_x = int(size * 0.62)
    spark_y = int(size * 0.21)
    spark_r = int(size * 0.035)
    draw.ellipse([(spark_x - spark_r, spark_y - spark_r), (spark_x + spark_r, spark_y + spark_r)], fill=(255, 209, 179, 255))

    return img

icon_256 = create_copper_icon(256)
icon_64 = icon_256.resize((64, 64), Image.Resampling.LANCZOS)
icon_32 = icon_256.resize((32, 32), Image.Resampling.LANCZOS)
icon_16 = icon_256.resize((16, 16), Image.Resampling.LANCZOS)

# Salva favicon.ico
icon_256.save(WORKSPACE_DIR / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (64, 64), (128, 128)])

# Salva PNG per browser e apple touch
icon_32.save(assets_dir / "favicon-32x32.png", format="PNG")
icon_16.save(assets_dir / "favicon-16x16.png", format="PNG")
icon_256.save(assets_dir / "apple-touch-icon.png", format="PNG")

print("Favicon files generated successfully: favicon.ico, assets/favicon-32x32.png, assets/apple-touch-icon.png")
