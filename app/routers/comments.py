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
from ..models import Comment, Post, User
from ..schemas import CommentCreate, CommentResponse
from ..services.notification_service import (
    send_comment_notification,
)


router = APIRouter(
    prefix="/posts",
    tags=["Comments"]
)


# =========================================================
# Add Comment
# =========================================================

@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # Check whether post exists
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Create comment
    # -----------------------------------------------------

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=comment_data.text
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # -----------------------------------------------------
    # Get post owner
    # -----------------------------------------------------

    post_owner = (
        db.query(User)
        .filter(
            User.id == post.author_id
        )
        .first()
    )

    # -----------------------------------------------------
    # Send notification in background
    # -----------------------------------------------------

    # Don't notify user when commenting on own post
    if (
        post_owner is not None
        and post_owner.id != current_user.id
    ):

        background_tasks.add_task(
    send_comment_notification,
    "sureshsuresh24062004@gmail.com",
    post.title,
    current_user.username,
    new_comment.created_at,
    new_comment.text
)

    return new_comment


# =========================================================
# Get Comments
# =========================================================

@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Check whether post exists
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Get comments
    # -----------------------------------------------------

    comments = (
        db.query(Comment)
        .filter(
            Comment.post_id == post_id
        )
        .order_by(
            Comment.created_at.asc()
        )
        .all()
    )

    return comments