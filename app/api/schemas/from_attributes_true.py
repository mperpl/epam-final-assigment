from pydantic import BaseModel, ConfigDict


class BaseResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
