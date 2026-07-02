import pytest

from lambda_function.utils.parse_s3_key import (
    PROCESSABLE_DOCUMENT_EXTENSIONS,
    PROCESSABLE_IMAGE_EXTENSIONS,
    parse_s3_key,
)


# --- 1. Valid Input Scenarios ---
@pytest.mark.parametrize(
    "s3_key, expected_category, expected_doc_id, expected_ext, expected_final_key",
    [
        # Case A: Standard Processable Image (.png -> .jpg conversion)
        # Case B: Standard Document File (.pdf -> keeps original extension)
        # Case C: Mixed Casing in Extension (.JpEg -> normalized to lowercase, outputs .jpg)
        # Case D: New Format Integration (.jfif -> outputs .jpg)
        ("raw/proj-123-uuid/doc-999.png", "images", "doc-999", ".jpg", "projects/images/proj-123-uuid/doc-999.jpg"),
        ("raw/proj-123-uuid/contract.pdf", "documents", "contract", ".pdf", "projects/documents/proj-123-uuid/contract.pdf"),
        ("raw/proj-123-uuid/photo.JpeG", "images", "photo", ".jpg", "projects/images/proj-123-uuid/photo.jpg"),
        ("raw/proj-123-uuid/asset.jfif", "images", "asset", ".jpg", "projects/images/proj-123-uuid/asset.jpg"),
    ]
)
def test_parse_s3_key_valid_cases(s3_key, expected_category, expected_doc_id, expected_ext, expected_final_key):
    result = parse_s3_key(s3_key)
    
    assert result["valid"] is True
    assert result["category"] == expected_category
    assert result["project_id"] == "proj-123-uuid"
    assert result["document_id"] == expected_doc_id
    assert result["extension"] == expected_ext
    assert result["final_key"] == expected_final_key


# --- 2. Invalid Input Scenarios (Validation Failures) ---
@pytest.mark.parametrize(
    "invalid_key, expected_reason",
    [
        # Case E: Wrong Root Prefix (Old path style instead of 'raw')
        # Case F: Deeply Nested Path (Too many directories)
        # Case G: Shallow Path (Missing filename or project directory)
        ("projects/images/proj-123-uuid/photo.jpg", "Path 'projects/images/proj-123-uuid/photo.jpg' does not match expected landing prefix."),
        ("raw/proj-123-uuid/subfolder/file.pdf", "Path 'raw/proj-123-uuid/subfolder/file.pdf' does not match expected landing prefix."),
        ("raw/file.pdf", "Path 'raw/file.pdf' does not match expected landing prefix."),
    ]
)
def test_parse_s3_key_invalid_path_cases(invalid_key, expected_reason):
    result = parse_s3_key(invalid_key)
    
    assert result["valid"] is False
    assert result["reason"] == expected_reason


# --- 3. Explicit Extension Type Denied Cases ---
@pytest.mark.parametrize(
    "unsupported_key",
    [   
        # Cases with illegal extensions
        "raw/proj-123-uuid/script.py",
        "raw/proj-123-uuid/audio.mp3",
        "raw/proj-123-uuid/README",
        "raw/proj-123-uuid/backup.tar.gz",
        "raw/proj-123-uuid/.gitignore",
    ]
)
def test_parse_s3_key_unsupported_extensions(unsupported_key):
    result = parse_s3_key(unsupported_key)
    
    assert result["valid"] is False
    assert "File type not allowed." in result["reason"]
    assert str(PROCESSABLE_IMAGE_EXTENSIONS) in result["reason"]
    assert str(PROCESSABLE_DOCUMENT_EXTENSIONS) in result["reason"]