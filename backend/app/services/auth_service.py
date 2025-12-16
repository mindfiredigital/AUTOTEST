from sqlalchemy.orm import Session
from app.schemas.auth_schema import RegisterRequest, RegisterResponse,LoginRequest,LoginResponse
from app.models.user import User
from app.models.role import Role
from app.config.security import security_service   
from fastapi import HTTPException, status, Response, Request
from app.config.setting import settings
from app.config.logger import logger



class AuthService:

    def register(self, data: RegisterRequest, db: Session) -> RegisterResponse:
        """
        Handles user registration:
        - Validate unique username & email
        - Hash password
        - Assign default role (e.g., 'user')
        - Save new user
        - Return response schema
        """
        logger.info(f"Registration attempt for email={data.email}")
        name = f"{data.firstname} {data.lastname}"


        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            logger.warning(f"Registration failed: email already exists ({data.email})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        existing_username = db.query(User).filter(User.username == data.username).first()
        if existing_username:
            logger.warning(f"Registration failed: username '{data.username}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )


        default_role = db.query(Role).filter(Role.type == "user").first()
        if not default_role:
            logger.error("Default role 'user' not found in Role table")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default role 'user' not found in Role table"
            )

        hashed_password = security_service.hash_password(data.password)


        new_user = User(
            username=data.username,
            password=hashed_password,
            name=name,
            email=data.email,
            role_id=default_role.id,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: user_id={new_user.id}, email={new_user.email}")

        return RegisterResponse(
            name=new_user.name,
            email=new_user.email,
            role=default_role.type
        )
    def login(self,response: Response, data: LoginRequest, db: Session) -> LoginResponse:
        """
        Logs in the user, verifies credentials, generates JWT access & refresh tokens,
        and stores them in secure HttpOnly cookies.
        Returns basic user details or raises an error if authentication fails.
        """
        logger.info(f"Login attempt for email={data.email}")
        user = db.query(User).filter(User.email == data.email).first()

        if not user:
            logger.warning(f"Login failed: user not found ({data.email})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or password"
            )

        if not security_service.verify_password(data.password, user.password):
            logger.warning(f"Login failed: Incorrect password for email={data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password"
            )

        access_token = security_service.create_access_token(
            subject=user.email,
            user_id=user.id,
            role_id=user.role_id
        )
        refresh_token = security_service.create_refresh_token(
            subject=user.email,
            user_id=user.id,
            role_id=user.role_id
        )
        role = db.query(Role).filter(Role.id == user.role_id).first()
        response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
        )
        logger.info(f"Login successful: user_id={user.id}, email={user.email}")
        return LoginResponse(
            name=user.name,
            email=user.email,
            role=role.type if role else None
        )
        
    def refresh(self, request: Request, response: Response) -> dict:
        """
        Refreshes the access token using the valid refresh token stored in cookies.
        Generates a new access token and updates the cookie.

        Raises an error if the refresh token is missing or invalid.
         """
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            logger.warning("Refresh token missing in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )

        try:
            payload = security_service.decode_token(refresh_token)
            if payload.get("type") != "refresh":
                logger.warning("Invalid refresh token type used")
                raise Exception("Invalid token type")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        new_access_token = security_service.create_access_token(
            subject=payload["sub"],
            user_id=payload["user_id"],
            role_id=payload["role_id"]
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        logger.info(f"Access token refreshed for user_id={payload['user_id']}")


        return {"message": "Access token refreshed"}


    def get_me(self, request: Request, db: Session, user: User):
        """
        Returns the authenticated user's profile details including id, name, email,
        and role. Assumes the user is already validated by authentication middleware.
        """
        logger.info(f"User profile accessed: user_id={user.id}")
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": db.query(Role).filter(Role.id == user.role_id).first().type
        }

    def logout(self, response: Response):
        """
        Logs out the user by deleting access and refresh token cookies.
        Returns a success message after clearing authentication cookies.
        """
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        logger.info("User logged out successfully")
        return {"message": "Logged out successfully"}
auth_service = AuthService()
