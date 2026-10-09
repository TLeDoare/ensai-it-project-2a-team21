from pydantic import BaseModel, EmailStr, constr

from business_object.types import Role


class PersonModel(BaseModel):
    id: int
    email: EmailStr
    role: Role


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class RegisterModel(BaseModel):
    email: EmailStr
    password: str
    role: Role

