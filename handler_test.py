import base64
import hashlib
import math
import random
from io import BytesIO

import runpod
from PIL import Image, ImageDraw, ImageFilter


def handler(event):
    input_data = event.get("input", {}) or {}
    prompt = input_data.get("prompt", "test image")
    width = int(input_data.get("width", 768))
    height = int(input_data.get("height", 512))

    # Clamp to keep this lightweight for fast endpoint validation.
    width = max(128, min(width, 1024))
    height = max(128, min(height, 1024))

    seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
    rnd = random.Random(seed)

    # Neon cyber palette inspired by cloud/GPU dashboards.
    c1 = (8, 16, 34)
    c2 = (25, 36, 70)
    accent_a = (0, 224, 255)
    accent_b = (127, 86, 255)
    accent_c = (255, 75, 214)

    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Vertical gradient background (deep blue).
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Soft neon glow orbs.
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(8):
        radius = rnd.randint(max(40, width // 12), max(80, width // 4))
        x = rnd.randint(-radius, width)
        y = rnd.randint(-radius, height)
        palette = [accent_a, accent_b, accent_c]
        base = palette[i % len(palette)]
        color = (base[0], base[1], base[2], rnd.randint(28, 70))
        gd.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=max(8, width // 80)))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    # Futuristic grid lines.
    draw = ImageDraw.Draw(img)
    spacing = max(28, width // 28)
    for x in range(0, width, spacing):
        alpha = 26 if (x // spacing) % 3 else 48
        draw.line([(x, 0), (x, height)], fill=(72, 95, 150, alpha), width=1)
    for y in range(0, height, spacing):
        alpha = 18 if (y // spacing) % 3 else 34
        draw.line([(0, y), (width, y)], fill=(72, 95, 150, alpha), width=1)

    # Top-right hex badge.
    badge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    cx = width - max(64, width // 11)
    cy = max(64, height // 7)
    rr = max(30, min(width, height) // 14)
    points = []
    for k in range(6):
        ang = math.radians(60 * k - 30)
        points.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    bd.polygon(points, outline=(0, 224, 255, 220), width=4, fill=(8, 14, 28, 120))
    bd.line((cx - rr * 0.35, cy, cx + rr * 0.2, cy), fill=(255, 75, 214, 220), width=4)
    bd.line((cx + rr * 0.2, cy, cx - rr * 0.05, cy + rr * 0.32), fill=(255, 75, 214, 220), width=4)
    badge = badge.filter(ImageFilter.GaussianBlur(radius=0.3))
    img = Image.alpha_composite(img.convert("RGBA"), badge).convert("RGB")

    # Frosted text panel.
    draw = ImageDraw.Draw(img)
    margin = max(20, width // 30)
    card_w = min(width - margin * 2, int(width * 0.78))
    card_h = min(height - margin * 2, int(height * 0.26))
    card_x0 = margin
    card_y0 = height - card_h - margin
    card_x1 = card_x0 + card_w
    card_y1 = card_y0 + card_h
    draw.rounded_rectangle(
        (card_x0, card_y0, card_x1, card_y1),
        radius=max(14, width // 50),
        fill=(7, 12, 26),
        outline=(0, 224, 255),
        width=2,
    )
    draw.text((card_x0 + 18, card_y0 + 14), "RUNPOD STYLE TEST", fill=(255, 255, 255))
    draw.text((card_x0 + 18, card_y0 + 44), f"prompt: {prompt[:90]}", fill=(180, 238, 255))

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return {
        "status": "success",
        "mode": "test-handler",
        "image_base64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
    }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
