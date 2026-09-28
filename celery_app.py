from celery import Celery

celery = Celery(
    "blog_management",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery.conf.update(
    timezone="UTC",
    enable_utc=True,
    imports=("app.celery_tasks",),
)

celery.conf.beat_schedule = {
    "publish-scheduled-posts-every-minute": {
        "task": "app.celery_tasks.publish_scheduled_posts",
        "schedule": 60.0,
    },
}
celery.conf.imports = ("app.celery_tasks",)