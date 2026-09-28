from celery import shared_task
from datetime import datetime

from app.database import SessionLocal
from app.models import Post


@shared_task(name="app.celery_tasks.publish_scheduled_posts")
def publish_scheduled_posts():
    db = SessionLocal()

    try:
        now = datetime.now()

        posts = (
            db.query(Post)
            .filter(
                Post.status == "scheduled",
                Post.scheduled_at <= now
            )
            .all()
        )

        count = 0

        for post in posts:
            post.status = "published"
            post.published_at = now
            count += 1

        db.commit()

        return f"{count} scheduled post(s) published"

    finally:
        db.close()