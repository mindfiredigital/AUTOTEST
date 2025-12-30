from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text 

from app.config.setting import settings
from app.routers.auth import router as auth_router
from app.db.session import get_db
def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        debug=settings.DEBUG
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root():
        """Basic root endpoint for API confirmation."""
        return {"message": f"{settings.PROJECT_NAME} is running successfully!"}

    @app.get("/api/v1/healthcheck")
    def health_check(db: Session = Depends(get_db)):
        """
        API health check endpoint that verifies database connectivity.
        """
        try:
            db.execute(text("SELECT 1")) 
            return {"status": "healthy", "database_connection": "successful"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection failed: {str(e)}"
            )
            
    # from app.api.routers import users
    # app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(auth_router, prefix="/api/v1/auth")
    


    return app

app = create_app()
