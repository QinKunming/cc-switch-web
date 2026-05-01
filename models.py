"""Pydantic models for API request/response."""
from typing import Optional, Any
from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    name: str
    settings_config: dict
    website_url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    icon: Optional[str] = None
    icon_color: Optional[str] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    settings_config: Optional[dict] = None
    website_url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    icon: Optional[str] = None
    icon_color: Optional[str] = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    app_type: str
    settings_config: dict
    website_url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    is_current: bool = False


class SwitchResult(BaseModel):
    success: bool
    message: str
    warnings: list[str] = []


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str
    captcha_answer: str


class PresetResponse(BaseModel):
    id: str
    name: str
    category: str
    website_url: Optional[str] = None
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    settings_config: dict
