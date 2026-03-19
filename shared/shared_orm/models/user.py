from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from shared_orm.db.base import Base

class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(200), nullable=False)  # store bcrypt hash
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role = relationship("Role")

    @validates("password")
    def validate_password_is_hashed(self, key, value):
        if value and not value.startswith("$2b$") and not value.startswith("$2a$"):
            raise ValueError(
                "User.password must be a bcrypt hash. "
                "Hash the password with bcrypt before assigning it."
            )
        return value
