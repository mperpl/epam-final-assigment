import mimetypes
import os
import re

from fastapi import UploadFile

from app.core.exceptions import AppException, DataIntegrityError
from app.core.settings import settings


def get_file_extension_if_allowed(filename: str, allowed_extensions: set = settings.ALLOWED_EXTENSIONS) -> str:
    _, file_extension = os.path.splitext(filename.lower())
    if file_extension not in allowed_extensions:
        raise DataIntegrityError(f"Unsupported file extension '{file_extension}'. Allowed: {', '.join(allowed_extensions)}")
    return file_extension


def get_safe_filename(filename: str) -> str:
    filename = filename.strip()
    if not filename:
        raise DataIntegrityError("Filename cannot be empty.")
    
    safe_name = os.path.basename(filename)
    base, ext = os.path.splitext(safe_name)
    re_safe_base = re.sub(r'[^a-zA-Z0-9_\-\s]', '', base).strip()
    if base != re_safe_base or not re_safe_base:
        raise DataIntegrityError("Filename is not safe.")

    return f"{re_safe_base}{ext}"


def get_content_type(filename) -> str:
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "application/octet-stream"
    return content_type


def validate_upload_file_size(file: UploadFile, max_size: int = settings.MAX_ALLOWED_FILE_SIZE_B):
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size:
        max_size_mb = max_size / (1_048_576)
        raise AppException(status_code=413, message=f"File size exceeds the maximum allowed limit of {max_size_mb:.1f} MB.")
