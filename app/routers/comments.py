from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..email_service import send_email
from ..models import Comment, Post, User
from ..schemas import CommentCreate, CommentResponse


router = APIRouter(
    prefix="/posts",
    tags=["Comments"]
)


# -------------------------
# Add Comment
# -------------------------

@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
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

    # Create comment
    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=comment_data.text
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Get post owner
    post_owner = (
        db.query(User)
        .filter(User.id == post.author_id)
        .first()
    )

    # Send email notification
    # Do not send notification when commenting on own post
    if (
        post_owner is not None
        and post_owner.id != current_user.id
    ):
        send_email(
            # Mailtrap demo domain allows sending only
            # to the Mailtrap account owner's email
            to_email="sureshsuresh24062004@gmail.com",

            subject="New Comment on Your Blog",

            body=(
                f"Hello {post_owner.username},\n\n"
                f"{current_user.username} commented on "
                f"your blog post:\n\n"
                f"Title: {post.title}\n"
                f"Comment: {comment_data.text}\n\n"
                f"Regards,\n"
                f"Blog Management API"
            )
        )

    return new_comment


# -------------------------
# Get Comments
# -------------------------

@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
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

    # Get comments
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments