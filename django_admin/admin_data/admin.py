from django.contrib import admin

from .models import SubscriptionPlan, BillingHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "post_limit",
        "image_limit",
        "like_limit",
        "comment_limit",
        "duration_days",
    )


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "subscription_plan_id",
        "price",
        "start_date",
        "end_date",
        "transaction_id",
        "created_at",
    )