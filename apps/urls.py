import debug_toolbar
from django.contrib import admin
from django.urls import path, include

from apps.core.utils import pong
from settings.document import document_urls
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ping/", pong),
    path("api/v1/", include("apps.user.urls")),
    path("api/v1/", include("apps.channel.urls")),
    path("api/v1/", include("apps.notice.urls")),
    path("api/v1/", include("apps.event.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
]


urlpatterns += document_urls
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
