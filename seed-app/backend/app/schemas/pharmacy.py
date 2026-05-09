from pydantic import BaseModel, ConfigDict


class PharmacyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    pharmacy_type: str
