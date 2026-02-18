#!/usr/bin/env python3
"""
TRELLIS API to Xonotic IQM Pipeline

Submits an image to the TRELLIS API server (192.168.0.103:8088),
waits for 3D generation, downloads GLB, and converts to IQM.

Usage:
    python3 api_to_xonotic.py image.png model_name [--scale 0.5]
"""

import os
import sys
import time
import argparse
import requests
import subprocess
from pathlib import Path

# Configuration
API_URL = "http://192.168.0.103:8088"
SCRIPT_DIR = Path(__file__).parent.resolve()
TRELLIS_TO_XONOTIC = SCRIPT_DIR / "trellis_to_xonotic.py"
POLL_INTERVAL = 5  # seconds
MAX_WAIT = 600  # 10 minutes

def submit_generation(api_url, image_path):
    """Submit image to API for 3D generation"""
    print(f"Submitting image: {image_path}")

    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f)}
        response = requests.post(f"{api_url}/generate/object", files=files)

    if response.status_code != 202:
        raise RuntimeError(f"API error: {response.text}")

    data = response.json()
    print(f"Task submitted: {data['task_id']}")
    return data['task_id']

def wait_for_completion(api_url, task_id):
    """Poll API until task completes"""
    print(f"Waiting for generation to complete...")

    start = time.time()
    while time.time() - start < MAX_WAIT:
        response = requests.get(f"{api_url}/task/{task_id}")
        data = response.json()

        status = data.get('status')
        print(f"  Status: {status}")

        if status == 'completed':
            return data
        elif status == 'failed':
            raise RuntimeError(f"Generation failed: {data.get('error')}")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError("Generation timed out after 10 minutes")

def download_glb(api_url, task_id, output_path):
    """Download GLB from API"""
    print(f"Downloading GLB to: {output_path}")

    response = requests.get(f"{api_url}/download/{task_id}/glb", stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Download failed: {response.text}")

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded: {os.path.getsize(output_path)} bytes")
    return output_path

def convert_to_iqm(glb_path, model_name, scale=None, rotate=None):
    """Convert GLB to Xonotic IQM"""
    cmd = [sys.executable, str(TRELLIS_TO_XONOTIC), str(glb_path), model_name]

    if scale:
        cmd.extend(["--scale", str(scale)])
    if rotate:
        cmd.extend(["--rotate", rotate])

    print(f"Converting to IQM: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        raise RuntimeError("IQM conversion failed")

def main():
    parser = argparse.ArgumentParser(description="Generate Xonotic model from image via TRELLIS API")
    parser.add_argument("image", help="Input image file")
    parser.add_argument("model_name", help="Output model name")
    parser.add_argument("--scale", type=float, default=None, help="Scale factor")
    parser.add_argument("--rotate", type=str, default=None, help="Rotation X,Y,Z degrees")
    parser.add_argument("--api-url", type=str, default=API_URL, help="API server URL")

    args = parser.parse_args()

    api_url = args.api_url

    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    # Check API health
    try:
        health = requests.get(f"{api_url}/health", timeout=5)
        if health.status_code != 200:
            raise ConnectionError("API not healthy")
        print(f"API server: {api_url} (healthy)")
    except Exception as e:
        print(f"Error: Cannot connect to API at {api_url}: {e}")
        sys.exit(1)

    try:
        # Step 1: Submit to API
        task_id = submit_generation(api_url, image_path)

        # Step 2: Wait for completion
        result = wait_for_completion(api_url, task_id)

        # Step 3: Download GLB
        glb_path = Path(f"/tmp/{args.model_name}.glb")
        download_glb(api_url, task_id, glb_path)

        # Step 4: Convert to IQM
        convert_to_iqm(glb_path, args.model_name, args.scale, args.rotate)

        print(f"\n✓ Model ready: /home/scott/Games/Xonotic/pk3_build/models/{args.model_name}/")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
