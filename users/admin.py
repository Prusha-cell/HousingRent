from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):   # admin.StackedInline рисует поля профиля под полями пользователя.
    model = UserProfile                         # говорит, что именно эту модель UserProfile мы показываем внутри User
    can_delete = False                          # can_delete - отключает возможность удалить профиль прямо из inline.
    verbose_name_plural = 'Profile'


# Расширяем стандартный UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)              # сначала удаляем стандартную регистрацию unregister(User) в админке,
admin.site.register(User, UserAdmin)     # затем снова регистрируем, но уже с нашим кастомным UserAdmin,
                                         # где подключён профиль.

# class UserProfileInline(admin.StackedInline):
#     model = UserProfile
#     can_delete = False
#     verbose_name_plural = 'Profile'
#     fk_name = 'user'
#
#
# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     # добавляем инлайн с профилем
#     inlines = (UserProfileInline,)
#
#     # расширяем столбцы списка пользователей
#     list_display = (
#         'username',
#         'email',
#         'first_name',
#         'last_name',
#         'get_role',
#         'is_staff',
#     )
#     list_select_related = ('profile',)  # чтобы не делать лишних запросов
#
#     def get_role(self, obj):
#         # вернёт значение поля role из связанного UserProfile
#         return obj.profile.role
#     get_role.short_description = 'Role'
#     get_role.admin_order_field = 'profile__role'