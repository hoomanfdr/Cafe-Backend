from django.urls import path

from .views import (
    OrderListAPIView,
    OrderDetailAPIView,
    CreateOrderAPIView,
    CancelOrderAPIView,
)

urlpatterns = [
    path("", OrderListAPIView.as_view(), name="order-list"),

    path("create/", CreateOrderAPIView.as_view(), name="create-order"),

    path("<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),

    path(
        "<int:pk>/cancel/",
        CancelOrderAPIView.as_view(),
        name="cancel-order",
    ),
]