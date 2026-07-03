from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # db
    DB_URL: Optional[str] = None
    VALKEY_URL: Optional[str] = None

    # jwt
    REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = None
    SECRET_KEY: Optional[str] = None
    ALGORITHM: Optional[str] = None

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET: Optional[str] = None

    # DOCUMENTS
    MAX_ALLOWED_FILE_SIZE_B: Optional[int] = None
    MAX_ALLOWED_PROJECT_SIZE_B: Optional[int] = None
    ALLOWED_DOCUMENT_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".pptx", ".xlsx"}
    ALLOWED_IMAGE_EXTENSIONS: set = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
        ".jfif",
    }
    ALLOWED_EXTENSIONS: set = ALLOWED_IMAGE_EXTENSIONS.union(
        ALLOWED_DOCUMENT_EXTENSIONS
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True, extra="ignore")


settings = Settings()
