"""Global session state — user yang sedang login."""
from typing import Optional


class Session:
    _user: Optional[dict] = None

    @classmethod
    def login(cls, user: dict) -> None:
        cls._user = dict(user)

    @classmethod
    def logout(cls) -> None:
        cls._user = None

    @classmethod
    def get(cls) -> Optional[dict]:
        return cls._user

    @classmethod
    def is_admin(cls) -> bool:
        return bool(cls._user and cls._user.get("is_admin"))

    @classmethod
    def username(cls) -> str:
        return cls._user["username"] if cls._user else ""

    @classmethod
    def nama(cls) -> str:
        return cls._user.get("nama_lengkap", "") if cls._user else ""

    @classmethod
    def must_change_password(cls) -> bool:
        return bool(cls._user and cls._user.get("must_change_password"))
