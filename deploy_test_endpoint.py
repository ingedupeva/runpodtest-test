#!/usr/bin/env python3
import argparse
import base64
import json
import os
import time
from pathlib import Path

import runpod


def find_endpoint_by_name(name: str):
    for endpoint in runpod.get_endpoints():
        if endpoint.get("name") == name:
            return endpoint
    return None


def create_or_reuse_endpoint(
    endpoint_name: str,
    template_name: str,
    image: str,
    gpu: str,
    disk_gb: int,
):
    existing = find_endpoint_by_name(endpoint_name)
    if existing:
        return {
            "endpoint_id": existing["id"],
            "template_id": existing.get("templateId"),
            "reused": True,
        }

    template = runpod.create_template(
        name=template_name,
        image_name=image,
        container_disk_in_gb=disk_gb,
        is_serverless=True,
    )
    endpoint = runpod.create_endpoint(
        name=endpoint_name,
        template_id=template["id"],
        gpu_ids=gpu,
        workers_min=0,
        workers_max=1,
        scaler_type="QUEUE_DELAY",
        scaler_value=4,
    )
    return {
        "endpoint_id": endpoint["id"],
        "template_id": template["id"],
        "reused": False,
    }


def run_test_job(endpoint_id: str, prompt: str, output_path: Path):
    endpoint = runpod.Endpoint(endpoint_id)
    job = endpoint.run(
        {
            "input": {
                "prompt": prompt,
                "width": 768,
                "height": 512,
            }
        }
    )
    print(json.dumps({"job_id": job.job_id}, ensure_ascii=False))

    final = "UNKNOWN"
    for i in range(120):
        status = job.status()
        if i % 2 == 0:
            print(json.dumps({"poll": i + 1, "status": status}, ensure_ascii=False))
        if status in {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            final = status
            break
        time.sleep(3)

    result = job.output()
    print("FINAL_STATUS", final)
    print(json.dumps(result, ensure_ascii=False))

    if isinstance(result, dict) and result.get("status") == "success" and result.get("image_base64"):
        output_path.write_bytes(base64.b64decode(result["image_base64"]))
        print(f"IMAGE_SAVED {output_path}")
        return 0
    return 2


def main():
    parser = argparse.ArgumentParser(description="Create/reuse Runpod test endpoint and optionally run a test job.")
    parser.add_argument("--endpoint-name", default="runpodtest-test-endpoint")
    parser.add_argument("--template-name", default="runpodtest-test-template")
    parser.add_argument("--image", default="ingedupeva/runpodtest-test:latest")
    parser.add_argument("--gpu", default="AMPERE_16")
    parser.add_argument("--disk-gb", type=int, default=20)
    parser.add_argument("--run-job", action="store_true")
    parser.add_argument("--prompt", default="Imagen final cloud test Runpod")
    parser.add_argument("--output", default="runpod_cloud_test_output.png")
    args = parser.parse_args()

    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        raise SystemExit("RUNPOD_API_KEY is required.")
    runpod.api_key = api_key

    info = create_or_reuse_endpoint(
        endpoint_name=args.endpoint_name,
        template_name=args.template_name,
        image=args.image,
        gpu=args.gpu,
        disk_gb=args.disk_gb,
    )
    print(json.dumps(info, ensure_ascii=False))

    if not args.run_job:
        return 0

    output_path = Path(args.output).resolve()
    return run_test_job(info["endpoint_id"], args.prompt, output_path)


if __name__ == "__main__":
    raise SystemExit(main())
