from django.urls import path

from .views import CartAPIView, AddToCartAPIView

urlpatterns = [
    path("", CartAPIView.as_view(), name="cart"),
    path("add/<int:product_id>/", AddToCartAPIView.as_view(), name="add-to-cart"),
]