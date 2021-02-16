from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import NoticeIdViewSet
from apps.channel.views import ChannelViewSet
from rest_framework_nested import routers
from apps.channel.urls import router

app_name = 'notice'


notices_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
notices_router.register(r'notices', NoticeIdViewSet, basename='channel-notices')


urlpatterns = [
    path('', include(router.urls), name='notice_list'),
    path('', include(notices_router.urls), name='notice_detail'),
]