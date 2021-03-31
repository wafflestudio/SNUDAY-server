from django.urls import include, path
from rest_framework.routers import SimpleRouter
from apps.user.views import UserViewSet, send_email, verify_email
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = "user"

user_router = SimpleRouter()
user_router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("users/login/", TokenObtainPairView.as_view(), name="user-login"),
    path("users/refresh/", TokenRefreshView.as_view(), name="user-refresh"),
    path("users/mail/send/", send_email, name="user-mail-send"),
    path("users/mail/verify/", verify_email, name="user-mail-verify"),
    path("", include(user_router.urls)),
]
