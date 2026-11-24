from business_object.types import Role


class Person:
    def __init__(self, email: str, password: str, role: Role, access_token: str | None = None, id: int | None = None,
                 active: bool = True):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.access_token = access_token
        # Un compte désactivé est conservé en base mais ne peut plus se connecter (F1)
        self.active = active
