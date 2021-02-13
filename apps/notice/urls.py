from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import NoticeViewSet, NoticeIdViewSet

app_name = 'notice'

router = SimpleRouter()
router.register('notices', NoticeViewSet, basename='notices')

id_router = SimpleRouter()
id_router.register('', NoticeIdViewSet, basename='notice')

urlpatterns = [
    path('channels/<int:pk>/', include(router.urls)),
    path('channels/<int:pk>/notices/<int:pk_2>/', include(id_router.urls)),
]