
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# =========================================================
# USER SCHEMAS
# =========================================================

class UserRegister(BaseModel):

    username: str = Field(
        ...,
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=100
    )


class UserResponse(BaseModel):

    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


# =========================================================
# AUTHENTICATION
# =========================================================

class Token(BaseModel):

    access_token: str
    token_type: str


# =========================================================
# POST SCHEMAS
# =========================================================

class PostCreate(BaseModel):

    title: str = Field(
        ...,
        min_length=3,
        max_length=200
    )

    content: str = Field(
        ...,
        min_length=10
    )

    # -----------------------------------------------------
    # Publishing options
    # -----------------------------------------------------

    status: str = Field(
        default="published"
    )

    scheduled_at: datetime | None = None

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        allowed_statuses = {
            "draft",
            "scheduled",
            "published"
        }

        value = value.lower()

        if value not in allowed_statuses:

            raise ValueError(
                "Status must be draft, scheduled, or published"
            )

        return value


class PostUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200
    )

    content: str | None = Field(
        default=None,
        min_length=10
    )

    status: str | None = None

    scheduled_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):

        if value is None:
            return value

        allowed_statuses = {
            "draft",
            "scheduled",
            "published"
        }

        value = value.lower()

        if value not in allowed_statuses:

            raise ValueError(
                "Status must be draft, scheduled, or published"
            )

        return value


class PostResponse(BaseModel):

    id: int

    title: str

    content: str

    image_url: str | None = None

    author_id: int

    created_at: datetime

    status: str

    scheduled_at: datetime | None = None

    published_at: datetime | None = None

    class Config:
        from_attributes = True


# =========================================================
# POST LIST RESPONSE
# =========================================================

class PostListResponse(BaseModel):

    posts: list[PostResponse]

    total: int

    page: int

    limit: int

    total_pages: int


# =========================================================
# COMMENT SCHEMAS
# =========================================================

class CommentCreate(BaseModel):

    text: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


class CommentResponse(BaseModel):

    id: int

    post_id: int

    user_id: int

    text: str

    created_at: datetime

    class Config:
        from_attributes = True


# =========================================================
# LIKE SCHEMAS
# =========================================================

class LikeResponse(BaseModel):

    message: str

    post_id: int

    user_id: int


# =========================================================
# NOTIFICATION
# =========================================================

class NotificationResponse(BaseModel):

    id: int

    message: str

    notification_type: str

    is_read: bool

    created_at: datetime

    class Config:
        from_attributes = True

