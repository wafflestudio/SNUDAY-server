import debug_toolbar
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.user.urls')),
    path('api/v1/', include('apps.channel.urls')),
    path('api/v1/', include('apps.notice.urls')),

    path('__debug__/', include(debug_toolbar.urls)),
]
