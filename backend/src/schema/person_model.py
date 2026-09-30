from pydantic import BaseModel, EmailStr, constr


class PersonModel(BaseModel):
    id: int
    email: EmailStr
    role: Role  # à implémenter ou importer ?


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class RegisterModel(BaseModel):
    email: EmailStr
    password: constr
    role: Role
