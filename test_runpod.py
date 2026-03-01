#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
from datetime import datetime

import runpod


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "zknzdpw2uwfrqo")
    prompt = os.getenv(
        "RUNPOD_PROMPT",
        "A cinematic photo of a futuristic city at sunset, ultra detailed",
    )
    steps = int(os.getenv("RUNPOD_STEPS", "20"))
    guidance = float(os.getenv("RUNPOD_GUIDANCE", "3.5"))
    poll_seconds = int(os.getenv("RUNPOD_POLL_SECONDS", "5"))
    max_polls = int(os.getenv("RUNPOD_MAX_POLLS", "120"))

    if not api_key:
        print(f"[{now()}] ERROR: RUNPOD_API_KEY is missing.")
        return 1

    runpod.api_key = api_key
    endpoint = runpod.Endpoint(endpoint_id)

    payload = {
        "input": {
            "prompt": prompt,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
        }
    }

    print(f"[{now()}] Endpoint: {endpoint_id}")
    print(f"[{now()}] Sending job...")
    job = endpoint.run(payload)
    print(f"[{now()}] Job ID: {job.job_id}")

    final_status = "UNKNOWN"
    for i in range(max_polls):
        status = job.status()
        print(f"[{now()}] Poll {i + 1}/{max_polls} -> {status}")
        if status in {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            final_status = status
            break
        time.sleep(poll_seconds)

    output = job.output()
    print(f"[{now()}] Final status: {final_status}")
    print(f"[{now()}] Raw output:")
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if isinstance(output, dict) and output.get("status") == "success" and output.get("image_base64"):
        image_bytes = base64.b64decode(output["image_base64"])
        out_path = os.path.abspath("runpod_output.png")
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        print(f"[{now()}] Image saved at: {out_path}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
