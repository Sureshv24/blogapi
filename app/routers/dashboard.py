from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import User, Post, Comment, Like

router = APIRouter(
    prefix="/user",
    tags=["Dashboard"]
)


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # User's posts
    posts = (
        db.query(Post)
        .filter(Post.author_id == current_user.id)
        .all()
    )

    # Total posts created by the user
    total_posts = len(posts)

    # Total comments made by the user
    total_comments = (
        db.query(Comment)
        .filter(Comment.user_id == current_user.id)
        .count()
    )

    # Total likes received on user's posts
    total_likes_received = (
        db.query(Like)
        .join(Post, Like.post_id == Post.id)
        .filter(Post.author_id == current_user.id)
        .count()
    )

    # Per-post statistics
    post_statistics = []

    for post in posts:
        likes = (
            db.query(Like)
            .filter(Like.post_id == post.id)
            .count()
        )

        comments = (
            db.query(Comment)
            .filter(Comment.post_id == post.id)
            .count()
        )

        post_statistics.append({
            "post_id": post.id,
            "title": post.title,
            "likes": likes,
            "comments": comments
        })

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_likes_received": total_likes_received,
        "total_views": 0,
        "post_statistics": post_statistics
    }