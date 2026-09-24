from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import User, AIChatHistory


router = APIRouter(
    prefix="/api/ai-support",
    tags=["AI Support"]
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class AISupportRequest(BaseModel):
    message: str


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class AISupportResponse(BaseModel):
    user_message: str
    response: str


# =========================================================
# AI SUPPORT ENDPOINT
# =========================================================

@router.post(
    "/",
    response_model=AISupportResponse
)
def ai_support(
    request: AISupportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    message = request.message.lower().strip()

    # =====================================================
    # CREATE POST
    # =====================================================

    if (
        "create post" in message
        or "create a post" in message
        or "how to create post" in message
    ):

        response = (
            "To create a post, go to the Posts section and select "
            "the Create Post option. Enter your title and content, "
            "then submit the post."
        )

    # =====================================================
    # EDIT POST
    # =====================================================

    elif (
        "edit post" in message
        or "update post" in message
        or "how to edit post" in message
    ):

        response = (
            "To edit a post, open your post and select the Edit option. "
            "Update the required details and save your changes."
        )

    # =====================================================
    # DELETE POST
    # =====================================================

    elif (
        "delete post" in message
        or "remove post" in message
        or "how to delete post" in message
    ):

        response = (
            "To delete a post, open your post and select the Delete option. "
            "Only the post owner can delete their own post."
        )

    # =====================================================
    # SUBSCRIPTION
    # =====================================================

    elif (
        "subscription" in message
        or "subscribe" in message
    ):

        response = (
            "You can manage your subscription from the Subscription section. "
            "Your active plan contains information about its price, duration "
            "and available limits."
        )

    # =====================================================
    # BILLING
    # =====================================================

    elif (
        "billing" in message
        or "payment" in message
        or "invoice" in message
    ):

        response = (
            "You can view your billing information and previous transactions "
            "from the Billing section of your account."
        )

    # =====================================================
    # PROFILE
    # =====================================================

    elif (
        "profile" in message
        or "account" in message
        or "username" in message
    ):

        response = (
            "You can manage your account information from your profile "
            "section. Your username and email are associated with your account."
        )

    # =====================================================
    # DASHBOARD / ANALYTICS
    # =====================================================

    elif (
        "dashboard" in message
        or "analytics" in message
        or "statistics" in message
    ):

        response = (
            "The dashboard provides analytics about your blog activity, "
            "including posts, likes, comments and other account information."
        )

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    elif (
        "notification" in message
        or "notifications" in message
        or "bell" in message
    ):

        response = (
            "Notifications keep you informed about activities such as likes, "
            "comments and subscription updates. You can mark notifications "
            "as read or unread from the notification center."
        )

    # =====================================================
    # GREETING
    # =====================================================

    elif any(
        word in message.split()
        for word in ["hi", "hello", "hey"]
    ):

        response = (
            f"Hello {current_user.username}! 👋 "
            "I'm your AI Support Assistant. "
            "I can help you with posts, subscriptions, billing, "
            "notifications and dashboard questions."
        )

    # =====================================================
    # GENERAL HELP
    # =====================================================

    elif (
        "help" in message
        or "what can you do" in message
        or "support" in message
    ):

        response = (
            "I can help you with creating, editing or deleting posts, "
            "subscriptions, billing, profile management, dashboard analytics "
            "and notifications."
        )

    # =====================================================
    # DEFAULT RESPONSE
    # =====================================================

    else:

        response = (
            "I'm here to help! You can ask me about creating, editing or "
            "deleting posts, subscriptions, billing, your profile, "
            "dashboard analytics or notifications."
        )

    # =====================================================
    # SAVE ACTIVITY / CHAT HISTORY
    # =====================================================

    chat_history = AIChatHistory(
        user_id=current_user.id,
        question=request.message,
        ai_response=response
    )

    db.add(chat_history)
    db.commit()

    # =====================================================
    # RETURN RESPONSE
    # =====================================================

    return {
        "user_message": request.message,
        "response": response
    }