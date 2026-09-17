import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import BillingHistory, SubscriptionPlan, User


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"]
)


# =========================================================
# Invoice Configuration
# =========================================================

INVOICE_DIR = "media/invoices"

os.makedirs(
    INVOICE_DIR,
    exist_ok=True
)


# =========================================================
# Generate Invoice PDF
# =========================================================

def generate_invoice(
    user: User,
    plan: SubscriptionPlan,
    start_date: datetime,
    end_date: datetime,
    transaction_id: str
) -> str:

    filename = f"invoice_{transaction_id}.pdf"

    file_path = os.path.join(
        INVOICE_DIR,
        filename
    )

    pdf = canvas.Canvas(
        file_path,
        pagesize=A4
    )

    width, height = A4

    # -------------------------
    # Invoice Header
    # -------------------------

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        50,
        height - 60,
        "BLOG MANAGEMENT API"
    )

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        height - 100,
        "SUBSCRIPTION INVOICE"
    )

    # -------------------------
    # Invoice Details
    # -------------------------

    pdf.setFont(
        "Helvetica",
        11
    )

    y = height - 150

    pdf.drawString(
        50,
        y,
        f"User Name: {user.username}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Email: {user.email}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Plan: {plan.name}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Price: Rs. {plan.price}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Start Date: {start_date.strftime('%Y-%m-%d')}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"End Date: {end_date.strftime('%Y-%m-%d')}"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        f"Transaction ID: {transaction_id}"
    )

    # -------------------------
    # Status
    # -------------------------

    y -= 50

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        "Payment Status: PAID"
    )

    y -= 40

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        "This is a simulated invoice generated for the"
    )

    y -= 15

    pdf.drawString(
        50,
        y,
        "Blog Management subscription system."
    )

    # -------------------------
    # Footer
    # -------------------------

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        50,
        40,
        "Thank you for subscribing!"
    )

    pdf.save()

    return f"/media/invoices/{filename}"


# =========================================================
# Get Subscription Plans
# =========================================================

@router.get("/plans")
def get_subscription_plans(
    db: Session = Depends(get_db)
):
    plans = (
        db.query(SubscriptionPlan)
        .order_by(SubscriptionPlan.id)
        .all()
    )

    return {
        "plans": [
            {
                "id": plan.id,
                "name": plan.name,
                "price": plan.price,
                "post_limit": plan.post_limit,
                "image_limit": plan.image_limit,
                "like_limit": plan.like_limit,
                "comment_limit": plan.comment_limit,
                "duration_days": plan.duration_days
            }
            for plan in plans
        ]
    }


# =========================================================
# Subscribe to Plan
# =========================================================

@router.post("/subscribe/{plan_id}")
def subscribe_to_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Find plan
    plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.id == plan_id
        )
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )

    # -------------------------
    # Subscription Dates
    # -------------------------

    start_date = datetime.utcnow()

    end_date = start_date + timedelta(
        days=plan.duration_days
    )

    # -------------------------
    # Transaction ID
    # -------------------------

    transaction_id = (
        f"TXN-{uuid.uuid4().hex[:12].upper()}"
    )

    # -------------------------
    # Update User Subscription
    # -------------------------

    current_user.subscription_plan_id = plan.id

    current_user.subscription_start = start_date

    current_user.subscription_end = end_date

    # -------------------------
    # Generate Invoice
    # -------------------------

    invoice_path = generate_invoice(
        user=current_user,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id
    )

    # -------------------------
    # Billing History
    # -------------------------

    billing = BillingHistory(
        user_id=current_user.id,
        subscription_plan_id=plan.id,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id,
        invoice_path=invoice_path
    )

    db.add(billing)

    db.commit()

    db.refresh(billing)

    return {
        "message": "Subscription activated successfully",
        "user_id": current_user.id,
        "plan": plan.name,
        "price": plan.price,
        "start_date": start_date,
        "end_date": end_date,
        "transaction_id": transaction_id,
        "invoice_path": invoice_path
    }


# =========================================================
# My Active Subscription
# =========================================================

@router.get("/my-subscription")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.subscription_plan_id is None:
        return {
            "message": "You do not have an active subscription"
        }

    plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.id ==
            current_user.subscription_plan_id
        )
        .first()
    )

    if plan is None:
        return {
            "message": "Subscription plan not found"
        }

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "plan": plan.name,
        "price": plan.price,
        "start_date": current_user.subscription_start,
        "end_date": current_user.subscription_end,
        "post_limit": plan.post_limit,
        "image_limit": plan.image_limit,
        "like_limit": plan.like_limit,
        "comment_limit": plan.comment_limit
    }


# =========================================================
# Billing History
# =========================================================

@router.get("/billing-history")
def get_billing_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    history = (
        db.query(BillingHistory)
        .filter(
            BillingHistory.user_id ==
            current_user.id
        )
        .order_by(
            BillingHistory.created_at.desc()
        )
        .all()
    )

    return {
        "billing_history": [
            {
                "id": item.id,
                "plan": item.subscription_plan.name,
                "price": item.price,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "transaction_id": item.transaction_id,
                "invoice_path": item.invoice_path,
                "created_at": item.created_at
            }
            for item in history
        ]
    }