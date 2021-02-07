from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import NoticeViewSet

app_name = 'notice'

router = SimpleRouter()
router.register('notices', NoticeViewSet, basename='notices')

urlpatterns = [
    path('channels/<int:pk>/', include(router.urls)),
]