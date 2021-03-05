from django.urls import include, path
from rest_framework_nested import routers

from apps.channel.urls import router
from apps.user.urls import user_router
from apps.notice.views import NoticeIdViewSet, UserNoticeViewSet

app_name = "notice"

notices_router = routers.NestedSimpleRouter(router, r"channels", lookup="channel")
notices_router.register(r"notices", NoticeIdViewSet, basename="channel-notices")

user_notice_router = routers.NestedSimpleRouter(user_router, r"users", lookup="user")
user_notice_router.register("notices", UserNoticeViewSet, basename="user-notices")

urlpatterns = [
    path("", include(router.urls), name="notice_list"),
    path("", include(notices_router.urls), name="notice_detail"),
    path("", include(user_notice_router.urls), name="user-notices"),
]
