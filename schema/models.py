from pydantic import BaseModel
from datetime import datetime

class TableStruct(BaseModel):
    type: str
    title: str
    director: str
    cast: str
    country: str
    date_added: datetime
    release_year: int
    rating: str
    duration: str
    listed_in: str
    description: str

