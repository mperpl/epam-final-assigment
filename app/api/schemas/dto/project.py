from pydantic import BaseModel, Field


class ProjectCreateDTO(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str


class ProjectUpdateDTO(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str
