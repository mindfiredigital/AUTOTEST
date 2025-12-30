from fastapi import FastAPI
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.db.seed import seed_roles, seed_admin_user, seed_settings, seed_prompt_setting

# IMPORTANT: import models before create_all
from app import models  # noqa: F401  <- this executes model modules to register tables

app = FastAPI(title="AutoTest Backend")

@app.get("/")
def root():
    return {"status": "ok", "service": "AutoTest Backend"}

# Create tables
Base.metadata.create_all(bind=engine)

# Seed roles and admin on startup
@app.on_event("startup")
def startup_seed():
    db = SessionLocal()
    try:
        seed_roles(db)
        seed_admin_user(db)
        seed_settings(db)
        seed_prompt_setting(db)
    finally:
        db.close()

# Routers
app.include_router(auth_router)
app.include_router(users_router)
