from django.urls import path

from .views import CreatePaymentAPIView

urlpatterns = [
    path(
        "<int:order_id>/",
        CreatePaymentAPIView.as_view(),
        name="create-payment",
    ),
]