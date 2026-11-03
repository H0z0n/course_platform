from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ThemePreference, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    theme: ThemePreference


class PreferencesUpdate(BaseModel):
    theme: ThemePreference


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleUpdate(BaseModel):
    role: UserRole
