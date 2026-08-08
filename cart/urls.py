from django.urls import path

from .views import (
    CartAPIView,
    AddToCartAPIView,
    RemoveFromCartAPIView,
    ClearCartAPIView,
    CartTotalAPIView,
)

urlpatterns = [
    path(
        "",
        CartAPIView.as_view(),
        name="cart",
    ),

    path(
        "add/<int:product_id>/",
        AddToCartAPIView.as_view(),
        name="add-to-cart",
    ),

    path(
        "remove/<int:product_id>/",
        RemoveFromCartAPIView.as_view(),
        name="remove-from-cart",
    ),

    path(
        "clear/",
        ClearCartAPIView.as_view(),
        name="clear-cart",
    ),

    path(
        "total/",
        CartTotalAPIView.as_view(),
        name="cart-total",
    ),
]