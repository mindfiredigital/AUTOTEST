from sqlalchemy.orm import Session
from app.schemas.auth_schema import RegisterRequest, RegisterResponse
from app.models.user import User
from app.models.role import Role
from app.config.security import security_service   
from fastapi import HTTPException, status



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

auth_service = AuthService()
