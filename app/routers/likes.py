from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..email_service import send_email
from ..models import Like, Post, User
from ..schemas import LikeResponse


router = APIRouter(
    prefix="/posts",
    tags=["Likes"]
)


# -------------------------
# Like Post
# -------------------------

@router.post(
    "/{post_id}/like",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED
)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check whether post exists
    post = (
        db.query(Post)
        .filter(Post.id == post_id)
        .first()
    )

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check whether user already liked the post
    existing_like = (
        db.query(Like)
        .filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        )
        .first()
    )

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already liked this post"
        )

    # Create like
    new_like = Like(
        post_id=post_id,
        user_id=current_user.id
    )

    db.add(new_like)
    db.commit()

    # Get post owner
    post_owner = (
        db.query(User)
        .filter(User.id == post.author_id)
        .first()
    )

    # Send email notification
    # Do not notify when user likes their own post
    if (
        post_owner is not None
        and post_owner.id != current_user.id
    ):
        send_email(
            # Temporary Mailtrap demo recipient
            to_email="sureshsuresh24062004@gmail.com",

            subject="New Like on Your Blog",

            body=(
                f"Hello {post_owner.username},\n\n"
                f"{current_user.username} liked your blog post:\n\n"
                f"Title: {post.title}\n\n"
                f"Regards,\n"
                f"Blog Management API"
            )
        )

    return {
        "message": "Post liked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }


# -------------------------
# Unlike Post
# -------------------------

@router.delete(
    "/{post_id}/like",
    response_model=LikeResponse
)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find existing like
    existing_like = (
        db.query(Like)
        .filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        )
        .first()
    )

    if existing_like is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not liked this post"
        )

    # Delete like
    db.delete(existing_like)
    db.commit()

    return {
        "message": "Post unliked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }