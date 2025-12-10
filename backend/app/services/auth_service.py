from sqlalchemy.orm import Session
from app.schemas.auth_schema import RegisterRequest, RegisterResponse,LoginRequest,LoginResponse
from app.models.user import User
from app.models.role import Role
from app.config.security import security_service   
from fastapi import HTTPException, status, Response, Request
from app.config.setting import settings



class AuthService:

    def register(self, data: RegisterRequest, db: Session) -> RegisterResponse:
        """
        Handles user registration:
        - Build username
        - Validate unique username & email
        - Hash password
        - Assign default role (e.g., 'user')
        - Save new user
        - Return response schema
        """

        username = data.firstname.lower() + data.lastname[0].lower()
        name = f"{data.firstname} {data.lastname}"


        existing_email = db.query(User).filter(User.email == data.email).first()
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )


        default_role = db.query(Role).filter(Role.type == "user").first()
        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default role 'user' not found in Role table"
            )

        hashed_password = security_service.hash_password(data.password)


        new_user = User(
            username=username,
            password=hashed_password,
            name=name,
            email=data.email,
            role_id=default_role.id,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return RegisterResponse(
            name=new_user.name,
            email=new_user.email,
            role=default_role.type
        )
    def login(self,response: Response, data: LoginRequest, db: Session) -> LoginResponse:
        user = db.query(User).filter(User.email == data.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or password"
            )

        if not security_service.verify_password(data.password, user.password):
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
        return LoginResponse(
            name=user.name,
            email=user.email,
            role=role.type if role else None
        )
        
    def refresh(self, request: Request, response: Response) -> dict:
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )

        try:
            payload = security_service.decode_token(refresh_token)
            if payload.get("type") != "refresh":
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

        return {"message": "Access token refreshed"}


    def get_me(self, request: Request, db: Session, user: User):


        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": db.query(Role).filter(Role.id == user.role_id).first().type
        }

    def logout(self, response: Response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return {"message": "Logged out successfully"}
auth_service = AuthService()
