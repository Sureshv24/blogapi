from datetime import datetime

from .email_service import send_email


def send_comment_notification(
    recipient_email: str,
    post_title: str,
    username: str,
    timestamp: datetime,
    comment_text: str
):

    subject = "New Comment on Your Blog Post"

    body = f"""
Hello,

Someone commented on your blog post.

Post: {post_title}
User: {username}
Activity: Commented on your post
Time: {timestamp.strftime("%Y-%m-%d %I:%M %p")}
Comment: {comment_text}

Regards,
Blog Management API
"""

    send_email(
        to_email=recipient_email,
        subject=subject,
        body=body
    )


def send_like_notification(
    recipient_email: str,
    post_title: str,
    username: str,
    timestamp: datetime
):

    subject = "New Like on Your Blog Post"

    body = f"""
Hello,

Someone liked your blog post.

Post: {post_title}
User: {username}
Activity: Liked your post
Time: {timestamp.strftime("%Y-%m-%d %I:%M %p")}

Regards,
Blog Management API
"""

    send_email(
        to_email=recipient_email,
        subject=subject,
        body=body
    )