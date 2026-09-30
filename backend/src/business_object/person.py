from business_object.types import Role


class Person:
    def __init__(self, email: str, password: str, role: Role, access_token: str, id: int | None = None):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.access_token = access_token
