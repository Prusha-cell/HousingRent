from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    1) Смотрим, если запрос на /login/ или /logout/ — пропускаем без изменения.
    2) Читаем из cookies access_token и подставляем в заголовок Authorization.
    3) Если access истёк — пытаемся обновить его через refresh_token,
       кладём новые токены обратно в cookies и редиректим запрос к целевому view.
    """

    AUTH_PATHS = (
        '/api/login/',
        '/api/logout/',
    )

    def process_request(self, request):
        # 1) пропускаем auth-path’ы
        if request.path_info in self.AUTH_PATHS:
            return

        # 2) читаем access из cookie
        access = request.COOKIES.get('access_token')
        if access:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access}'

    def process_response(self, request, response):
        # если ответ 401 и в теле “Token is expired” — пробуем авторефреш
        if response.status_code == 401 and b'Token is expired' in response.content:
            refresh = request.COOKIES.get('refresh_token')
            if not refresh:
                return response

            # проверяем, что токен не заблэклистен
            if (OutstandingToken.objects.filter(token=refresh).exists() and
                    not BlacklistedToken.objects.filter(token__token=refresh).exists()):
                try:
                    new_refresh = RefreshToken(refresh)
                    new_access = str(new_refresh.access_token)
                    # если refresh сам ротационный — сохраняем его тоже
                    new_refresh = str(new_refresh) if hasattr(new_refresh, 'access_token') else refresh

                    # обновляем cookies
                    response.set_cookie('access_token', new_access,
                                        httponly=True, samesite='Lax')
                    response.set_cookie('refresh_token', new_refresh,
                                        httponly=True, samesite='Lax')

                    # повторно вызываем view с обновлённым заголовком
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access}'
                    view, args, kwargs = resolve(request.path_info)
                    new_response = view(request, *args, **kwargs)
                    new_response.set_cookie('access_token', new_access,
                                            httponly=True, samesite='Lax')
                    new_response.set_cookie('refresh_token', new_refresh,
                                            httponly=True, samesite='Lax')
                    new_response.render()
                    return new_response

                except TokenError:
                    # разлогиниваем
                    response.delete_cookie('access_token')
                    response.delete_cookie('refresh_token')
                    response.render()
                    return response

        return response
