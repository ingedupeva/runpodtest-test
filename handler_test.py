import base64
from io import BytesIO

import runpod
from PIL import Image, ImageDraw


def handler(event):
    input_data = event.get("input", {}) or {}
    prompt = input_data.get("prompt", "test image")
    width = int(input_data.get("width", 768))
    height = int(input_data.get("height", 512))

    # Clamp to keep this lightweight for fast endpoint validation.
    width = max(128, min(width, 1024))
    height = max(128, min(height, 1024))

    img = Image.new("RGB", (width, height), color=(20, 32, 56))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "RUNPOD TEST OK", fill=(255, 255, 255))
    draw.text((20, 55), f"prompt: {prompt[:80]}", fill=(200, 220, 255))

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return {
        "status": "success",
        "mode": "test-handler",
        "image_base64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
    }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
