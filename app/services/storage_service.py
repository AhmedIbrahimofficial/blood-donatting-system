"""
File storage service — Cloudflare R2 (S3-compatible) in production,
local disk in development.

Usage:
    path = storage_service.upload(file_bytes, filename, content_type)
    url  = storage_service.get_url(path)
"""
from __future__ import annotations

import logging
import os
import uuid

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Local upload dir (dev fallback)
_LOCAL_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "uploads",
)


def _get_s3_client():
    """Return a boto3 S3 client configured for Cloudflare R2 or AWS S3."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )


def upload_file(file_bytes: bytes, original_filename: str, content_type: str) -> str:
    """
    Upload a file and return its storage path/key.

    - If S3 credentials are configured → uploads to R2/S3
    - Otherwise → saves to local uploads/ folder (dev mode)

    Returns:
        str: The storage key (e.g. "uploads/abc123.pdf")
    """
    ext = os.path.splitext(original_filename)[-1].lower()
    key = f"uploads/{uuid.uuid4().hex}{ext}"

    if settings.S3_BUCKET_NAME and settings.S3_ACCESS_KEY_ID:
        try:
            s3 = _get_s3_client()
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            logger.info("Uploaded %s to R2/S3: %s", original_filename, key)
            return key
        except ClientError as exc:
            logger.error("S3 upload failed: %s — falling back to local", exc)

    # Local fallback
    os.makedirs(_LOCAL_UPLOAD_DIR, exist_ok=True)
    local_path = os.path.join(_LOCAL_UPLOAD_DIR, os.path.basename(key))
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    logger.info("Saved locally: %s", local_path)
    return key


def get_file_url(key: str) -> str:
    """
    Return a public URL for a stored file.

    - R2/S3: generates a pre-signed URL valid for 1 hour
    - Local: returns a relative path
    """
    if settings.S3_BUCKET_NAME and settings.S3_ACCESS_KEY_ID:
        try:
            s3 = _get_s3_client()
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )
            return url
        except ClientError as exc:
            logger.error("Failed to generate presigned URL: %s", exc)

    return f"/{key}"
