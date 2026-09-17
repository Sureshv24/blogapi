from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    # -----------------------------------------
    # Active Subscription
    # -----------------------------------------

    subscription_plan_id = Column(
        Integer,
        ForeignKey("subscription_plans.id"),
        nullable=True
    )

    subscription_start = Column(
        DateTime,
        nullable=True
    )

    subscription_end = Column(
        DateTime,
        nullable=True
    )

    # -----------------------------------------
    # Relationships
    # -----------------------------------------

    subscription_plan = relationship(
        "SubscriptionPlan",
        back_populates="users"
    )

    posts = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    billing_history = relationship(
        "BillingHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# =========================================================
# SUBSCRIPTION PLAN
# =========================================================

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False,
        default=0
    )

    # Maximum posts allowed
    # NULL = unlimited
    post_limit = Column(
        Integer,
        nullable=True
    )

    # Maximum images allowed
    # NULL = unlimited
    image_limit = Column(
        Integer,
        nullable=True
    )

    # Maximum likes allowed
    # NULL = unlimited
    like_limit = Column(
        Integer,
        nullable=True
    )

    # Maximum comments allowed
    # NULL = unlimited
    comment_limit = Column(
        Integer,
        nullable=True
    )

    duration_days = Column(
        Integer,
        nullable=False,
        default=30
    )

    # -----------------------------------------
    # Relationships
    # -----------------------------------------

    users = relationship(
        "User",
        back_populates="subscription_plan"
    )

    billing_history = relationship(
        "BillingHistory",
        back_populates="subscription_plan"
    )


# =========================================================
# BILLING HISTORY
# =========================================================

class BillingHistory(Base):
    __tablename__ = "billing_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    subscription_plan_id = Column(
        Integer,
        ForeignKey("subscription_plans.id"),
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False
    )

    start_date = Column(
        DateTime,
        nullable=False
    )

    end_date = Column(
        DateTime,
        nullable=False
    )

    transaction_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    invoice_path = Column(
        String(255),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------
    # Relationships
    # -----------------------------------------

    user = relationship(
        "User",
        back_populates="billing_history"
    )

    subscription_plan = relationship(
        "SubscriptionPlan",
        back_populates="billing_history"
    )


# =========================================================
# POST
# =========================================================

class Post(Base):
    __tablename__ = "posts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    # Uploaded image filename
    image = Column(
        String(255),
        nullable=True
    )

    author_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    @property
    def image_url(self):
        if self.image:
            return f"/media/posts/{self.image}"

        return None

    author = relationship(
        "User",
        back_populates="posts"
    )

    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )

    likes = relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan"
    )


# =========================================================
# COMMENT
# =========================================================

class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    post = relationship(
        "Post",
        back_populates="comments"
    )

    user = relationship(
        "User",
        back_populates="comments"
    )


# =========================================================
# LIKE
# =========================================================

class Like(Base):
    __tablename__ = "likes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    post = relationship(
        "Post",
        back_populates="likes"
    )

    user = relationship(
        "User",
        back_populates="likes"
    )

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "user_id",
            name="uq_like_post_user"
        ),
    )