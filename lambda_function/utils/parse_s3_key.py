import os

PROCESSABLE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jfif"}
PROCESSABLE_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx", ".xlsx"}


def parse_s3_key(s3_key: str) -> dict:
    path_parts = s3_key.split("/")

    if len(path_parts) != 3 or path_parts[0] != "raw":
        return {
            "valid": False,
            "reason": f"Path '{s3_key}' does not match expected landing prefix.",
        }

    project_id = path_parts[1]
    raw_filename = path_parts[2]
    document_id, extension = os.path.splitext(raw_filename)
    extension = extension.lower() if extension else ""

    if extension in PROCESSABLE_IMAGE_EXTENSIONS:
        category = "images"
        extension = ".jpg"
        final_filename = f"{document_id}{extension}"
    elif extension in PROCESSABLE_DOCUMENT_EXTENSIONS:
        category = "documents"
        final_filename = raw_filename
    else:
        return {
            "valid": False,
            "reason": f"File type not allowed.\nPROCESSABLE_IMAGE_EXTENSIONS: {PROCESSABLE_IMAGE_EXTENSIONS}\n\
                PROCESSABLE_DOCUMENT_EXTENSIONS: {PROCESSABLE_DOCUMENT_EXTENSIONS}",
        }

    final_key = f"projects/{category}/{project_id}/{final_filename}"

    return {
        "valid": True,
        "category": category,
        "project_id": project_id,
        "document_id": document_id,
        "extension": extension,
        "final_key": final_key,
    }
