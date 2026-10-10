from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RoleAssignment(BaseModel):
    roles: list[str]

class UserAdminResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    roles: list[str] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PlatformStats(BaseModel):
    total_users: int
    total_materials: int
    total_downloads: int
    active_users_last_30_days: int
