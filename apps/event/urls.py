from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import EventViewSet, UserEventViewSet
from apps.channel.views import ChannelViewSet
from rest_framework_nested import routers
from apps.channel.urls import router
from apps.user.urls import user_router


app_name = 'event'

events_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
events_router.register(r'events', EventViewSet, basename='channel-events')

user_event_router = routers.NestedSimpleRouter(user_router, r'users', lookup='user')
user_event_router.register('events', UserEventViewSet, basename='user-events')

urlpatterns = [
    path('', include(router.urls), name='event_list'),
    path('', include(events_router.urls), name='event_detail'),
    path('', include(user_event_router.urls), name= 'user-events')
]