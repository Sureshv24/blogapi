import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Post, User
from ..schemas import PostResponse


router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


# -------------------------
# Upload Configuration
# -------------------------

UPLOAD_DIR = "media/posts"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


# -------------------------
# Save Image
# -------------------------

def save_image(image: UploadFile) -> str:

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, WEBP and GIF images are allowed"
        )

    original_name = image.filename or "image"

    extension = os.path.splitext(
        original_name
    )[1].lower()

    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(file_path, "wb") as file:
        file.write(image.file.read())

    return filename


# -------------------------
# Delete Image
# -------------------------

def delete_image(filename: str | None):

    if not filename:
        return

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    if os.path.exists(file_path):
        os.remove(file_path)


# -------------------------
# Create Post
# -------------------------

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(
    title: str,
    content: str,
    image: UploadFile | None = File(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    image_filename = None

    if image is not None:
        image_filename = save_image(image)

    new_post = Post(
        title=title,
        content=content,
        image=image_filename,
        author_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


# -------------------------
# Get All Posts - Public
# -------------------------

@router.get(
    "",
    response_model=list[PostResponse]
)
def get_posts(
    db: Session = Depends(get_db)
):

    return (
        db.query(Post)
        .order_by(Post.created_at.desc())
        .all()
    )


# -------------------------
# Get My Posts
# -------------------------

@router.get(
    "/mine",
    response_model=list[PostResponse]
)
def get_my_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return (
        db.query(Post)
        .filter(
            Post.author_id == current_user.id
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )


# -------------------------
# Get Single Post - Public
# -------------------------

@router.get(
    "/{post_id}",
    response_model=PostResponse
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):

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

    return post


# -------------------------
# Update Own Post
# -------------------------

@router.put(
    "/{post_id}",
    response_model=PostResponse
)
def update_post(
    post_id: int,
    title: str,
    content: str,
    image: UploadFile | None = File(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

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

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own posts"
        )

    post.title = title
    post.content = content

    if image is not None:

        old_image = post.image

        new_image = save_image(image)

        post.image = new_image

        delete_image(old_image)

    db.commit()
    db.refresh(post)

    return post


# -------------------------
# Delete Own Post
# -------------------------

@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

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

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )

    # Delete image from media folder
    delete_image(post.image)

    db.delete(post)
    db.commit()

    return None