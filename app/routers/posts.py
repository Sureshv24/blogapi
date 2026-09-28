import os
import uuid
from math import ceil
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Post, User, SubscriptionPlan
from ..schemas import PostListResponse, PostResponse


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

UPLOAD_DIR = "media/posts"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
}


# =========================================================
# ALLOWED POST STATUS
# =========================================================

ALLOWED_STATUS = {
    "draft",
    "published",
    "scheduled",
}


# =========================================================
# SAVE IMAGE
# =========================================================

def save_image(image: UploadFile) -> str:

    original_name = image.filename or "image"

    extension = os.path.splitext(
        original_name
    )[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only JPG, JPEG, PNG, WEBP and GIF "
                "images are allowed"
            )
        )

    filename = f"{uuid.uuid4().hex}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    with open(file_path, "wb") as file:

        file.write(
            image.file.read()
        )

    return filename


# =========================================================
# DELETE IMAGE
# =========================================================

def delete_image(filename: str | None):

    if not filename:
        return

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    if os.path.exists(file_path):

        os.remove(file_path)


# =========================================================
# CREATE POST
# =========================================================

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(

    title: str = Form(...),

    content: str = Form(...),

    post_status: str = Form(
        default="published"
    ),

    scheduled_at: datetime | None = Form(
        default=None
    ),

    image: UploadFile | None = File(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    # =====================================================
    # Validate status
    # =====================================================

    post_status = post_status.lower().strip()

    if post_status not in ALLOWED_STATUS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid status. Use: "
                "draft, published or scheduled"
            )
        )

    # =====================================================
    # Validate scheduling
    # =====================================================

    now = datetime.utcnow()

    # -----------------------------------------------------
    # Draft
    # -----------------------------------------------------

    if post_status == "draft":

        if scheduled_at is not None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Draft posts cannot have "
                    "scheduled_at"
                )
            )

        final_status = "draft"

        final_published_at = None

    # -----------------------------------------------------
    # Scheduled
    # -----------------------------------------------------

    elif post_status == "scheduled":

        if scheduled_at is None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "scheduled_at is required "
                    "for scheduled posts"
                )
            )

        # Remove timezone information if supplied
        # because SQLite DateTime is currently naive.
        if scheduled_at.tzinfo is not None:

            scheduled_at = (
                scheduled_at
                .astimezone()
                .replace(tzinfo=None)
            )

        if scheduled_at <= now:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "scheduled_at must be "
                    "a future datetime"
                )
            )

        final_status = "scheduled"

        final_published_at = None

    # -----------------------------------------------------
    # Published immediately
    # -----------------------------------------------------

    else:

        if scheduled_at is not None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Published posts cannot have "
                    "scheduled_at"
                )
            )

        final_status = "published"

        final_published_at = now

    # =====================================================
    # Subscription Plan Check
    # =====================================================

    if current_user.subscription_plan_id is not None:

        plan = (
            db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.id
                == current_user.subscription_plan_id
            )
            .first()
        )

        if plan is not None:

            if plan.post_limit is not None:

                post_count = (
                    db.query(Post)
                    .filter(
                        Post.author_id
                        == current_user.id
                    )
                    .count()
                )

                if post_count >= plan.post_limit:

                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "You've reached your plan "
                            "limit. Kindly upgrade your "
                            "plan to continue."
                        )
                    )

    # =====================================================
    # Image Upload
    # =====================================================

    image_filename = None

    if image is not None:

        image_filename = save_image(
            image
        )

    # =====================================================
    # Create Post
    # =====================================================

    new_post = Post(

        title=title,

        content=content,

        image=image_filename,

        author_id=current_user.id,

        status=final_status,

        scheduled_at=scheduled_at,

        published_at=final_published_at
    )

    db.add(
        new_post
    )

    db.commit()

    db.refresh(
        new_post
    )

    return new_post


# =========================================================
# GET ALL POSTS
# Pagination + Search
# =========================================================

@router.get(
    "",
    response_model=PostListResponse
)
def get_posts(

    page: int = Query(
        1,
        ge=1
    ),

    limit: int = Query(
        10,
        ge=1,
        le=100
    ),

    search: str | None = Query(
        None
    ),

    db: Session = Depends(get_db)
):

    query = db.query(
        Post
    )

    # -----------------------------------------------------
    # Only published posts for public listing
    # -----------------------------------------------------

    query = query.filter(
        Post.status == "published"
    )

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if search:

        query = query.filter(

            (Post.title.ilike(
                f"%{search}%"
            ))

            |

            (Post.content.ilike(
                f"%{search}%"
            ))
        )

    # -----------------------------------------------------
    # Total
    # -----------------------------------------------------

    total = query.count()

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    posts = (
        query
        .order_by(
            Post.published_at.desc(),
            Post.created_at.desc()
        )
        .offset(
            (page - 1) * limit
        )
        .limit(
            limit
        )
        .all()
    )

    # -----------------------------------------------------
    # Total Pages
    # -----------------------------------------------------

    total_pages = (
        ceil(
            total / limit
        )
        if total > 0
        else 1
    )

    return {
        "posts": posts,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


# =========================================================
# GET MY POSTS
# =========================================================

@router.get(
    "/mine",
    response_model=list[PostResponse]
)
def get_my_posts(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(
            Post
        )
        .filter(
            Post.author_id
            == current_user.id
        )
        .order_by(
            Post.created_at.desc()
        )
        .all()
    )


# =========================================================
# GET SINGLE POST
# =========================================================

@router.get(
    "/{post_id}",
    response_model=PostResponse
)
def get_post(

    post_id: int,

    db: Session = Depends(get_db)
):

    post = (
        db.query(
            Post
        )
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

    return post


# =========================================================
# UPDATE OWN POST
# =========================================================

@router.put(
    "/{post_id}",
    response_model=PostResponse
)
def update_post(

    post_id: int,

    title: str = Form(...),

    content: str = Form(...),

    post_status: str | None = Form(
        default=None
    ),

    scheduled_at: datetime | None = Form(
        default=None
    ),

    image: UploadFile | None = File(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    post = (
        db.query(
            Post
        )
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

    # =====================================================
    # Ownership Check
    # =====================================================

    if post.author_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only update "
                "your own posts"
            )
        )

    # =====================================================
    # Update Text
    # =====================================================

    post.title = title

    post.content = content

    # =====================================================
    # Update Publishing Status
    # =====================================================

    if post_status is not None:

        post_status = (
            post_status
            .lower()
            .strip()
        )

        if post_status not in ALLOWED_STATUS:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid status. Use: "
                    "draft, published or scheduled"
                )
            )

        now = datetime.utcnow()

        # -------------------------------------------------
        # Draft
        # -------------------------------------------------

        if post_status == "draft":

            if scheduled_at is not None:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Draft posts cannot have "
                        "scheduled_at"
                    )
                )

            post.status = "draft"
            post.scheduled_at = None
            post.published_at = None

        # -------------------------------------------------
        # Scheduled
        # -------------------------------------------------

        elif post_status == "scheduled":

            if scheduled_at is None:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "scheduled_at is required "
                        "for scheduled posts"
                    )
                )

            if scheduled_at.tzinfo is not None:

                scheduled_at = (
                    scheduled_at
                    .astimezone()
                    .replace(tzinfo=None)
                )

            if scheduled_at <= now:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "scheduled_at must be "
                        "a future datetime"
                    )
                )

            post.status = "scheduled"
            post.scheduled_at = scheduled_at
            post.published_at = None

        # -------------------------------------------------
        # Published
        # -------------------------------------------------

        else:

            if scheduled_at is not None:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Published posts cannot have "
                        "scheduled_at"
                    )
                )

            post.status = "published"
            post.scheduled_at = None

            if post.published_at is None:

                post.published_at = now

    # =====================================================
    # Replace Image
    # =====================================================

    if image is not None:

        old_image = post.image

        new_image = save_image(
            image
        )

        post.image = new_image

        delete_image(
            old_image
        )

    # =====================================================
    # Save
    # =====================================================

    db.commit()

    db.refresh(
        post
    )

    return post


# =========================================================
# DELETE OWN POST
# =========================================================

@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_post(

    post_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )
):

    post = (
        db.query(
            Post
        )
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

    # =====================================================
    # Ownership Check
    # =====================================================

    if post.author_id != current_user.id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only delete "
                "your own posts"
            )
        )

    # =====================================================
    # Delete Image
    # =====================================================

    delete_image(
        post.image
    )

    # =====================================================
    # Delete Post
    # =====================================================

    db.delete(
        post
    )

    db.commit()

    return None