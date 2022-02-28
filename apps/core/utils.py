from functools import reduce

from django.shortcuts import _get_queryset
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


@api_view(["get"])
def pong(request):
    return Response("pongpingpongping!!")


def compose(*fs):
    def compose2(f, g):
        return lambda *a, **kw: f(g(*a, **kw))

    return reduce(compose2, fs, lambda x: x)


def get_object_or_400(klass, *args, **kwargs):
    """
    # `get_object_or_404`의 수정판
    * 존재하지 않으면 400
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, "get"):
        klass__name = (
            klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        )
        raise ValueError(
            "First argument to get_object_or_400() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise ValidationError("해당 객체가 없습니다.")
