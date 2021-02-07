from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    message = '매니저 권한이 필요합니다.'
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if obj.managers.filter(id=request.user.id).exists():
                return True
            elif request.method in ('GET'):
                return True
            return False
        else:
            return False
