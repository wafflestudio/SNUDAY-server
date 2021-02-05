from django.urls import include, path
from rest_framework.routers import SimpleRouter
from .views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'user'

router = SimpleRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('users/login/', TokenObtainPairView.as_view(), name='user-login'),
    path('users/refresh/', TokenRefreshView.as_view(), name='user-refresh'),
    path('', include(router.urls)),
]