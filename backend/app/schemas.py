from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

class LocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if not self.location.strip():
            raise ValueError("Location cannot be blank")
        if self.start_date > self.end_date:
            raise ValueError("Start date must be on or before end date")
        return self

class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    weather: dict
    created_at: datetime
    updated_at: datetime
