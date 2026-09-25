import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine
from . import models

from .routers import (
    auth,
    auth0,
    posts,
    comments,
    likes,
    subscriptions,
    dashboard,
    notifications,
    ai_support,
)

load_dotenv()

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

if not SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY is missing from .env")


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Blog Management API",
    description="Blog Management API using FastAPI and SQLite",
    version="1.0.0"
)


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
)


app.mount(
    "/dashboard",
    StaticFiles(
        directory="dashboard",
        html=True
    ),
    name="dashboard"
)

app.mount(
    "/media",
    StaticFiles(
        directory="media"
    ),
    name="media"
)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(ai_support.router)
app.include_router(auth0.router)


@app.get("/")
def root():
    return {
        "message": "Blog Management API is running"
    }