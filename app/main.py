from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from routers import auth
from config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Add SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to Koolix Backends"}