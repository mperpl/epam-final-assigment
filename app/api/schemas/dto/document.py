
from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import DataIntegrityError
from app.services.utils.file import get_safe_filename


class FilenameBase(BaseModel):
    filename: str = Field(max_length=255)

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        try:
            return get_safe_filename(v)
        except DataIntegrityError as e:
            raise ValueError(str(e))

class DocumentUpdateDTO(FilenameBase):
    pass