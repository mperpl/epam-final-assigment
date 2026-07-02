from pydantic import BaseModel


class DocumentCreateDTO(BaseModel):
    filename: str
    file_url: str
