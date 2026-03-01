import os
import base64
from io import BytesIO
import traceback

import runpod
import torch
from diffusers import DiffusionPipeline

MODEL_ID = "black-forest-labs/FLUX.1-dev"
pipe = None

def load_model():
    global pipe
    if pipe is not None:
        return pipe

    # Prevent xet-backed downloads issues on some ephemeral workers.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    hf_token = os.environ.get("HF_TOKEN")  # configúralo en Runpod si el modelo es gated

    print(f"Loading {MODEL_ID} on {device} dtype={dtype} ...")
    pipe = DiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        token=hf_token
    ).to(device)
    print("Model loaded successfully.")
    return pipe

def handler(event):
    input_data = event.get("input", {}) or {}
    prompt = input_data.get("prompt")

    if not prompt:
        return {"status": "error", "message": "No prompt provided in request input."}

    try:
        num_inference_steps = int(input_data.get("num_inference_steps", 28))
        guidance_scale = float(input_data.get("guidance_scale", 3.5))

        if not 1 <= num_inference_steps <= 100:
            return {
                "status": "error",
                "message": "num_inference_steps must be between 1 and 100."
            }
        if not 0.0 <= guidance_scale <= 20.0:
            return {
                "status": "error",
                "message": "guidance_scale must be between 0.0 and 20.0."
            }

        model = load_model()
        image = model(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        ).images[0]

        buffer = BytesIO()
        image.save(buffer, format="PNG")

        return {
            "status": "success",
            "image_base64": base64.b64encode(buffer.getvalue()).decode("utf-8")
        }
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid numeric input for num_inference_steps or guidance_scale."
        }
    except Exception:
        print("Unhandled inference error:")
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Internal error while generating the image."
        }

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
