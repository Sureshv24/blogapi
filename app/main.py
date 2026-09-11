from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers import auth, posts, comments, likes


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Blog Management API",
    description="Blog Management API using FastAPI and SQLite",
    version="1.0.0"
)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)

@app.get("/")
def root():
    return {
        "message": "Blog Management API is running"
    }