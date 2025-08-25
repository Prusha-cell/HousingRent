import logging
import time
import uuid

from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from config.logging_utils import request_id_ctx, user_id_ctx


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    1) If the request targets /login/ or /logout/, let it pass unchanged.
    2) Read access_token from cookies and inject it into the Authorization header.
    3) If the access token is expired, try to refresh it using refresh_token:
       put the new tokens back into cookies and re-dispatch the request to the target view.
    """

    AUTH_PATHS = (
        "/api/login/",
        "/api/logout/",
    )

    def process_request(self, request):
        # 1) Skip auth paths
        if request.path_info in self.AUTH_PATHS:
            return

        # 2) Read access token from cookies
        access = request.COOKIES.get("access_token")
        if access:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {access}"

    def process_response(self, request, response):
        # If the response is 401 and body says “Token is expired” — attempt auto-refresh
        if response.status_code == 401 and b"Token is expired" in response.content:
            refresh = request.COOKIES.get("refresh_token")
            if not refresh:
                return response

            # Ensure the refresh token exists and is not blacklisted
            if (
                OutstandingToken.objects.filter(token=refresh).exists()
                and not BlacklistedToken.objects.filter(token__token=refresh).exists()
            ):
                try:
                    new_refresh = RefreshToken(refresh)
                    new_access = str(new_refresh.access_token)
                    # If refresh is rotational, also persist the rotated refresh
                    new_refresh = str(new_refresh) if hasattr(new_refresh, "access_token") else refresh

                    # Update cookies
                    response.set_cookie("access_token", new_access, httponly=True, samesite="Lax")
                    response.set_cookie("refresh_token", new_refresh, httponly=True, samesite="Lax")

                    # Re-dispatch the view with a fresh Authorization header
                    request.META["HTTP_AUTHORIZATION"] = f"Bearer {new_access}"
                    view, args, kwargs = resolve(request.path_info)
                    new_response = view(request, *args, **kwargs)
                    new_response.set_cookie("access_token", new_access, httponly=True, samesite="Lax")
                    new_response.set_cookie("refresh_token", new_refresh, httponly=True, samesite="Lax")
                    new_response.render()
                    return new_response

                except TokenError:
                    # Logout: clear cookies
                    response.delete_cookie("access_token")
                    response.delete_cookie("refresh_token")
                    response.render()
                    return response

        return response


class RequestContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id_ctx.set(str(uuid.uuid4()))
        request._start_time = time.time()

    def process_response(self, request, response):
        try:
            # к этому моменту DRF уже мог обратиться к request.user
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                user_id_ctx.set(str(user.pk))
            else:
                user_id_ctx.set("-")

            duration_ms = int((time.time() - getattr(request, "_start_time", time.time())) * 1000)
            logging.getLogger("access").info(
                "%s %s -> %s (%dms)",
                getattr(request, "method", "-"),
                getattr(request, "path", "-"),
                getattr(response, "status_code", "-"),
                duration_ms,
            )
        finally:
            request_id_ctx.set("-")
            user_id_ctx.set("-")
        return response
