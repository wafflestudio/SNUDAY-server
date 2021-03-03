from rest_framework.permissions import BasePermission


class ManagerCanModify(BasePermission):
    message = "매니저 권한이 필요합니다."

    def has_object_permission(self, request, view, obj):
        if view.action in (
            "destroy",
            "partial_update",
            "update",
            "add_manager",
            "allow",
            "disallow",
        ):
            return obj.managers.filter(id=request.user.id).exists()
        return True
