from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import SessionLocal
import secrets

from app.admin.setup import admin
from app.core.config import settings
from app.routers import article as articles_router
from app.routers import auth as auth_router
from app.routers import comment as comments_router
from app.routers import tag as tags_router
from app.routers import user as users_router

app = FastAPI(title=settings.APP_NAME)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="admin_session",
    max_age=3600 * 24 * 7,  # 7 days
)


@app.middleware("http")
async def db_session_middleware(request, call_next):
    """Add database session to request state"""
    request.state.db = SessionLocal()
    try:
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


app.include_router(auth_router.router)
app.include_router(articles_router.router)
app.include_router(comments_router.router)
app.include_router(users_router.router)
app.include_router(tags_router.router)

admin.mount_to(app)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Medium Clone API"}
