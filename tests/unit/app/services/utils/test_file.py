import io
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile

from app.core.exceptions import (
    AppExceptionError,
    DataIntegrityError,
)
from app.services.utils.file import (
    get_content_type,
    get_file_extension_if_allowed,
    get_safe_filename,
    update_document_filename_validator,
    validate_upload_file_size,
)

MOCK_ALLOWED_EXTENTIONS = {".jpg", ".jpeg", ".png", ".pdf", ".docx"}


class TestGetFileExtensionIfAllowed:
    @pytest.mark.parametrize(
        "filename, expected_extension",
        [
            # Happy Paths
            ("document.pdf", ".pdf"),
            ("photo.jpg", ".jpg"),
            ("report.docx", ".docx"),
            # Case Normalization Check (Function runs filename.lower())
            ("IMAGE.PNG", ".png"),
            ("Resume.Pdf", ".pdf"),
            ("archive.JPEG", ".jpeg"),
            # Double Extension Behavior (Extracts only the final part)
            ("evil.exe.png", ".png"),
            ("backup.tar.jpg", ".jpg"),
        ],
    )
    def test_allowed_extensions_success(self, filename, expected_extension):
        """Verifies that valid and mixed-case extensions are properly extracted and matched."""
        result = get_file_extension_if_allowed(
            filename, allowed_extensions=MOCK_ALLOWED_EXTENTIONS
        )
        assert result == expected_extension

    @pytest.mark.parametrize(
        "invalid_filename",
        [
            # Blocked Exts
            ("malware.exe"),
            ("script.py"),
            ("payload.sh"),
            # Illegal
            ("no_extension_file"),
            (".gitignore"),
            ("trailing_dot."),
        ],
    )
    def test_disallowed_extensions_raises_error(self, invalid_filename):
        """Verifies that unauthorized extensions or files missing an extension throw DataIntegrityError."""
        with pytest.raises(DataIntegrityError) as exc_info:
            get_file_extension_if_allowed(
                invalid_filename, allowed_extensions=MOCK_ALLOWED_EXTENTIONS
            )

        assert "Unsupported file extension" in str(exc_info.value)


class TestGetSafeFilename:
    @pytest.mark.parametrize(
        "filename, expected_safe_name",
        [
            # Happy Path Scenarios
            ("analytics_report_2026.csv", "analytics_report_2026.csv"),
            ("user-profile-v3.png", "user-profile-v3.png"),
            # Spaces Handling (Spaces are explicitly allowed by your regex \s)
            ("my legacy document.docx", "my legacy document.docx"),
            (
                "  padded_name.pdf  ",
                "padded_name.pdf",
            ),  # Trimming leading/trailing whitespace
        ],
    )
    def test_safe_filenames_success(self, filename, expected_safe_name):
        """Verifies that pristine and structurally safe filenames return exactly as expected."""
        assert get_safe_filename(filename) == expected_safe_name

    @pytest.mark.parametrize(
        "dangerous_filename, expected_error_msg",
        [
            # Empty and Whitespace Inputs
            ("", "Filename cannot be empty."),
            ("     ", "Filename cannot be empty."),
            # Injected Special Characters (Triggers regex mismatch)
            ("photo$profile!.png", "Filename is not safe."),
            ("invoice#123[draft].xlsx", "Filename is not safe."),
            ("test<script>alert(1)</script>.html", "Filename is not safe."),
            # Pure Symbol Overwrites (Triggers empty re_safe_base guard)
            ("!@#$%^&*.jpg", "Filename is not safe."),
            ("..png", "Filename is not safe."),
        ],
    )
    def test_unsafe_filenames_raises_error(
        self, dangerous_filename, expected_error_msg
    ):
        """Verifies that malicious, empty, or symbol-corrupted names throw DataIntegrityError."""
        with pytest.raises(DataIntegrityError) as exc_info:
            get_safe_filename(dangerous_filename)

        assert str(exc_info.value) == expected_error_msg


class TestGetContentType:
    @pytest.mark.parametrize(
        "filename, expected_content_type",
        [
            # Scenario 1, 2, & 3: Standard Known Mime Types
            ("avatar.png", "image/png"),
            ("invoice.pdf", "application/pdf"),
            ("notes.txt", "text/plain"),
            # Case Insensitivity Verification (mimetypes handles this natively)
            ("PHOTO.JPEG", "image/jpeg"),
            # Scenario 4 & 5: Unknown/Missing Extensions (Triggers Fallback Guard)
            ("dataset.unrecognized_ext", "application/octet-stream"),
            ("README", "application/octet-stream"),
        ],
    )
    def test_get_content_type_scenarios(self, filename, expected_content_type):
        """Verifies that standard extensions are resolved correctly and unknown extensions drop back safely."""
        assert get_content_type(filename) == expected_content_type


ONE_MB = 1_048_576
class TestValidateUploadFileSize:
    def test_file_size_within_limit_success(self):
        """Verifies that files under or equal to the maximum allowed size pass through cleanly."""
        # Arrange: Setup an in-memory stream with 500 KB of dummy data
        file_stream = io.BytesIO(b"\x00" * 512_000)
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.file = file_stream

        validate_upload_file_size(mock_upload_file, max_size=ONE_MB)

        # Assert: Critical check! The file pointer must be reset back to 0
        assert file_stream.tell() == 0

    def test_file_size_exactly_at_limit_success(self):
        """Verifies that a file preccisely at the boundary limit is accepted."""
        file_stream = io.BytesIO(b"\x00" * ONE_MB)
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.file = file_stream

        validate_upload_file_size(mock_upload_file, max_size=ONE_MB)

        assert file_stream.tell() == 0

    def test_file_size_exceeds_limit_raises_error(self):
        """Verifies that a file over the limit throws a 413 AppExceptionError with a clear MB readout."""
        # Arrange: Setup an in-memory stream with 2.5 MB of dummy data
        file_size_bytes = int(2.5 * ONE_MB)
        file_stream = io.BytesIO(b"\x00" * file_size_bytes)
        mock_upload_file = MagicMock(spec=UploadFile)
        mock_upload_file.file = file_stream

        with pytest.raises(AppExceptionError) as exc_info:
            validate_upload_file_size(mock_upload_file, max_size=ONE_MB)

        assert exc_info.value.status_code == 413
        assert "exceeds the maximum allowed limit of 1.0 MB" in exc_info.value.message

class MockSettings:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".png"}
settings = MockSettings()
class TestUpdateDocumentFilenameValidator:
    def test_valid_filename_update(self):
        # Should pass
        update_document_filename_validator("test.pdf", "new_name.pdf")

    def test_case_insensitive_extension_update(self):
        # .JPG and .jpg should be treated as equal
        update_document_filename_validator("test.JPG", "new_name.jpg")

    def test_illegal_extension_change(self):
        # Changing from pdf to docx
        with pytest.raises(DataIntegrityError, match="Extension change not allowed"):
            update_document_filename_validator("test.pdf", "test.docx")

    def test_unsupported_extension(self):
        # Attempting to use a non-allowed extension
        with pytest.raises(DataIntegrityError, match='Extension change not allowed. Must remain test.pdf'):
            update_document_filename_validator("test.pdf", "test.exe")

    def test_no_extension_to_extension(self):
        # Logic should handle cases where one might lack an extension
        with pytest.raises(DataIntegrityError):
            update_document_filename_validator("test", "test.pdf")