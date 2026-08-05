"""Routes de l'app 'payments'."""

from django.urls import path

from .views import (
    InitiatePaymentView,
    InstructorSalesSummaryView,
    MyPaymentsView,
    MyPayoutsView,
    MySubscriptionsView,
    PaymentWebhookView,
    SubscriptionPlanListView,
)

app_name = "payments"

urlpatterns = [
    path("plans/", SubscriptionPlanListView.as_view(), name="plans"),
    path("initiate/", InitiatePaymentView.as_view(), name="initiate"),
    path("webhook/<str:provider>/", PaymentWebhookView.as_view(), name="webhook"),
    path("my-payments/", MyPaymentsView.as_view(), name="my-payments"),
    path("my-subscriptions/", MySubscriptionsView.as_view(), name="my-subscriptions"),
    path("my-payouts/", MyPayoutsView.as_view(), name="my-payouts"),
    path("my-sales-summary/", InstructorSalesSummaryView.as_view(), name="my-sales-summary"),
]
