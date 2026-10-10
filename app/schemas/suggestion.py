from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

class SuggestionBase(BaseModel):
    suggestion_type: str
    field_name: str | None = None
    current_value: str | None = None
    proposed_value: str | None = None
    reason: str | None = None

class SuggestionCreate(SuggestionBase):
    pass

class SuggestionResponse(SuggestionBase):
    id: str
    material_id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SuggestionReview(BaseModel):
    action: Literal["approved", "rejected"]
    notes: str | None = None