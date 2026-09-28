from datetime import datetime

from app.database import SessionLocal
from app.models import Post


def publish_scheduled_posts():
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        posts = (
            db.query(Post)
            .filter(
                Post.status == "scheduled",
                Post.scheduled_at <= now
            )
            .all()
        )

        for post in posts:
            post.status = "published"
            post.published_at = now
            post.scheduled_at = None

        db.commit()

        return len(posts)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()