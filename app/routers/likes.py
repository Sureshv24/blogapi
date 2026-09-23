from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import (
    Like,
    Post,
    User,
    Notification,
)
from ..schemas import LikeResponse

from ..services.notification_service import (
    send_like_notification,
)


router = APIRouter(
    prefix="/posts",
    tags=["Likes"]
)


# =========================================================
# LIKE POST
# =========================================================

@router.post(
    "/{post_id}/like",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED
)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Check whether post exists
    # -----------------------------------------------------

    post = (
        db.query(Post)
        .filter(
            Post.id == post_id
        )
        .first()
    )

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # -----------------------------------------------------
    # Check whether user already liked the post
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Create Like
    # -----------------------------------------------------

    new_like = Like(
        post_id=post_id,
        user_id=current_user.id
    )

    db.add(new_like)

    # -----------------------------------------------------
    # Get Post Owner
    # -----------------------------------------------------

    post_owner = (
        db.query(User)
        .filter(
            User.id == post.author_id
        )
        .first()
    )

    # -----------------------------------------------------
    # Create In-App Notification
    # -----------------------------------------------------

    if (
        post_owner is not None
        and post_owner.id != current_user.id
    ):

        new_notification = Notification(
            user_id=post_owner.id,
            message=(
                f"{current_user.username} liked "
                f"your post '{post.title}'"
            ),
            notification_type="like",
            is_read=False,
            created_at=datetime.utcnow()
        )

        db.add(new_notification)

    # -----------------------------------------------------
    # Save Like + In-App Notification
    # -----------------------------------------------------

    db.commit()

    db.refresh(new_like)

    # -----------------------------------------------------
    # EXISTING SMTP EMAIL NOTIFICATION
    # -----------------------------------------------------
    #
    # IMPORTANT:
    # This keeps your existing personal inbox.
    #
    # When someone likes your post, the email will still
    # be sent to:
    #
    # sureshsuresh24062004@gmail.com
    #
    # Your existing notification_service.py will handle
    # SMTP/Mailtrap sending.
    # -----------------------------------------------------

    if (
        post_owner is not None
        and post_owner.id != current_user.id
    ):

        background_tasks.add_task(
            send_like_notification,

            # Existing SMTP inbox
            "sureshsuresh24062004@gmail.com",

            # Post title
            post.title,

            # Person who liked
            current_user.username,

            # Time
            datetime.utcnow()
        )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Post liked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }


# =========================================================
# UNLIKE POST
# =========================================================

@router.delete(
    "/{post_id}/like",
    response_model=LikeResponse
)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Find Existing Like
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Delete Like
    # -----------------------------------------------------

    db.delete(existing_like)

    db.commit()

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Post unliked successfully",
        "post_id": post_id,
        "user_id": current_user.id
    }