from django.contrib import admin

from .models import InstructorPayout, Payment, Subscription, SubscriptionPlan


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["reference", "student", "provider", "amount", "status", "initiated_at"]
    list_filter = ["provider", "status", "purpose"]
    search_fields = ["reference", "student__email", "provider_transaction_id"]
    readonly_fields = ["reference", "provider_response_payload", "initiated_at"]


admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
admin.site.register(InstructorPayout)
