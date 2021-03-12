from django.urls import re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

description = """
SNUDAY의 API 문서입니다.
"""

schema_view = get_schema_view(
    openapi.Info(
        title="SNUDAY API",
        default_version="v1",
        description=description,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="heka1024@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

document_urls = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
