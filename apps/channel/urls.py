from django.urls import include, path
from rest_framework.routers import SimpleRouter
from apps.channel.views import ChannelViewSet, ChannelSearchViewSet

app_name = "channel"

router = SimpleRouter()
router.register("channels", ChannelViewSet, basename="channel")
router.register("search", ChannelSearchViewSet, basename="search")

urlpatterns = [
    path("", include(router.urls)),
]
