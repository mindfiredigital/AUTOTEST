from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from app.config.setting import settings


class SecurityService:
    """
    Handles password hashing, verification,
    JWT token creation and decoding.
    """

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.ALGO
        self.default_exp_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES


    def hash_password(self, password: str) -> str:
        """Hash a plain password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its bcrypt hash."""
        return self.pwd_context.verify(plain_password, hashed_password)


    def create_access_token(
        self,
        *,
        subject: str,
        user_id: int,
        role_id: int,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token."""

        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.default_exp_minutes)
        )

        payload = {
            "sub": subject,
            "exp": expire,
            "user_id": user_id,
            "role_id": role_id,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


    def decode_token(self, token: str) -> dict:
        """Decode a JWT token and return its payload."""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


security_service = SecurityService()
