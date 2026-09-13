import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.STANDARD
    modules: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    modules: list[str] | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    modules: list[str]
    is_active: bool
