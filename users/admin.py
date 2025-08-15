from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
                                         # admin.StackedInline renders profile fields below the user fields.
    model = UserProfile                  # show this model inline inside User
    can_delete = False                   # disable deleting the profile from the inline
    verbose_name_plural = 'Profile'


# Extend the default UserAdmin to include the profile inline
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Unregister the default User admin and register our customized one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)