from pydantic import BaseModel
from typing import Optional, Dict


class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingsOut(BaseModel):
    settings: Dict[str, str]


class PermissionSet(BaseModel):
    user_id: int
    module: str
    can_read: bool
    can_write: bool


class PermissionOut(BaseModel):
    id: int
    user_id: int
    module: str
    can_read: bool
    can_write: bool

    class Config:
        from_attributes = True


class EmailTestRequest(BaseModel):
    to_email: str
