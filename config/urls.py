from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/cart/", include("cart.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payment/", include("payment.urls")),

    # Products API
    path("api/", include("products.urls")),


    # Users API
    path("api/", include("users.urls")),

    # JWT Authentication
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]