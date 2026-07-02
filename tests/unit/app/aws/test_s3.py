import pytest

from app.aws.s3 import s3_key_generator
from app.core.exceptions import DataIntegrityError


# ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.jfif'}
# ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.docx', '.txt', '.pptx', '.xlsx'}
class TestS3KeyGenerator:
# --- 1. Valid Cases (Images & Documents) ---
    @pytest.mark.parametrize(
        "project_id, document_id, file_extension, base_folder, expected_path",
        [
            # Case A: Standard Image (.png -> normalized and forced to .jpg)
            # Case B: Mixed Casing Image (.JfIf -> normalized and forced to .jpg)
            # Case C: Standard Document (.pdf -> keeps original extension)
            # Case D: Mixed Casing Document (.DoCx -> normalized to lowercase)
            # Case E: Custom Base Folder Override
            ("p1", "d1", ".png", "projects", "projects/images/p1/d1.jpg"),
            ("p1", "d1", ".JfIf", "projects", "projects/images/p1/d1.jpg"),
            ("p1", "doc-file", ".pdf", "projects", "projects/documents/p1/doc-file.pdf"),
            ("p1", "doc-file", ".DoCx", "projects", "projects/documents/p1/doc-file.docx"),
            ("p1", "d1", ".png", "archive", "archive/images/p1/d1.jpg"),    
        ]
    )
    def test_s3_key_generator_success(self, project_id, document_id, file_extension, base_folder, expected_path):
        result = s3_key_generator(
            project_id=project_id,
            document_id=document_id,
            file_extension=file_extension,
            base_folder=base_folder
        )
        assert result == expected_path


    # --- 2. Invalid / Error Cases ---
    @pytest.mark.parametrize(
        "invalid_extension",
        [
            # Case F: Completely Unsupported Extension
            # --""--
            # Case G: Missing Dot / Empty String
            (".mp3"),
            (".exe"),
            (""),
        ]
    )
    def test_s3_key_generator_invalid_extensions(self, invalid_extension):
        # Verify that your DataIntegrityError exception is explicitly raised
        with pytest.raises(DataIntegrityError) as exc_info:
            s3_key_generator(
                project_id="p1",
                document_id="d1",
                file_extension=invalid_extension
            )
        
        assert str(exc_info.value) == "Invalid file extension."