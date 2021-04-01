from django.urls import include, path
from rest_framework.routers import SimpleRouter
from apps.user.views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = "user"

user_router = SimpleRouter()
user_router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("users/login/", TokenObtainPairView.as_view(), name="user-login"),
    path("users/refresh/", TokenRefreshView.as_view(), name="user-refresh"),
    path(
        "users/",
        UserViewSet.as_view(
            {
                "post": "create",
            }
        ),
    ),
    path(
        "users/<user_pk>/",
        UserViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "update",
            }
        ),
    ),
    path(
        "users/<user_pk>/subscribing_channels/",
        UserViewSet.as_view(
            {
                "get": "subscribing_channels",
            }
        ),
    ),
    path(
        "users/<user_pk>/managing_channels/",
        UserViewSet.as_view({"get": "managing_channels"}),
    ),
]
