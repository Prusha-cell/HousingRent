from django.db.models.deletion import ProtectedError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        blocked = [str(obj) for obj in getattr(exc, "protected_objects", [])]
        return Response(
            {
                "detail": "Cannot delete object: there are related records.",
                "blocked_by": blocked,
                "code": "protected"
            },
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
