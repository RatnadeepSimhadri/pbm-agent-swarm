from pydantic import BaseModel, ConfigDict


class PrescriberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    npi: str
    specialty: str
    phone: str
    full_name: str
