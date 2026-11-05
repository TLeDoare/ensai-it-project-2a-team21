import re

from pydantic import BaseModel, EmailStr, Field

from business_object.types import Role

PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)'
    r'(?=.*[!@#$%^&*(),.?":{}|<>_\-+=])'
    r'[A-Za-z\d!@#$%^&*(),.?":{}|<>_\-+=]{8,}$'
)


class PersonModel(BaseModel):
    id: int
    email: EmailStr
    role: Role


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class RegisterModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, pattern=PASSWORD_REGEX)
    role: Role


class UpdateModel(BaseModel):
    id: int
    email: EmailStr
    password: str
