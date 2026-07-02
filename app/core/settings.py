from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # db
    DB_URL: str
    VALKEY_URL: str

    # jwt
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SECRET_KEY: str
    ALGORITHM: str

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET: str

    # DOCUMENTS
    MAX_ALLOWED_FILE_SIZE_B: int
    MAX_ALLOWED_PROJECT_SIZE_B: int
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
