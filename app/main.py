from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth as auth_router
from app.routers import article as articles_router
from app.routers import comment as comments_router
from app.routers import user as users_router
from app.routers import tag as tags_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.APP_NAME)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router)
app.include_router(articles_router.router)
app.include_router(comments_router.router)
app.include_router(users_router.router)
app.include_router(tags_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Medium Clone API"}
