from rest_framework.pagination import CursorPagination


class IDCursorPagination(CursorPagination):
    """
    # ID 기반 페이지네이터
    * page size는 10,
    * order by id desc,
    """

    page_size = 10
    ordering = "-id"


class IssuedDateCursorPagination(CursorPagination):
    """
    # ID 기반 페이지네이터
    * page size는 10,
    * order by issued_date desc,
    """

    page_size = 10
    ordering = "-issued_date"
