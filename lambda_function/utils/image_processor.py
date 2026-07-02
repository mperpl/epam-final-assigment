# lambda/utils/image_processor.py
import io
import os

import boto3

try:
    from PIL import Image
except ImportError:
    Image = None

s3_client = boto3.client("s3")

MAX_WIDTH = 1920
MAX_HEIGHT = 1080
try:
    MAX_WIDTH = int(os.environ.get("MAX_IMAGE_WIDTH", 1920))
    MAX_HEIGHT = int(os.environ.get("MAX_IMAGE_HEIGHT", 1080))
except ValueError:
    print(
        "Warning: Malformed environment configuration detected. Falling back to default thresholds."
    )


def process_and_route_image(bucket_name: str, src_key: str, dest_key: str) -> bool:
    if Image is None:
        print("CRITICAL: Pillow library is missing. Attach a Lambda Layer.")
        return False

    response = s3_client.get_object(Bucket=bucket_name, Key=src_key)
    raw_bytes = response["Body"].read()

    img = Image.open(io.BytesIO(raw_bytes))

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        print(
            f"Resizing asset from {width}x{height} to fit within {MAX_WIDTH}x{MAX_HEIGHT}"
        )
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)

    s3_client.put_object(
        Bucket=bucket_name,
        Key=dest_key,
        Body=buffer,
        ContentType="image/jpeg",
        Metadata={"optimized": "true"},
    )

    s3_client.delete_object(Bucket=bucket_name, Key=src_key)
    print(f"Successfully processed and moved raw asset to permanent home: {dest_key}")
    return True
