from django.conf import settings

from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token


class MyAdminSite(AdminSite):
    site_header = ugettext_lazy(settings.SITE_TITLE)
    site_title = ugettext_lazy(settings.SITE_TITLE)
    index_title = ugettext_lazy("Detailed administration")


TokenAdmin.raw_id_fields = ("user",)

admin_site = MyAdminSite()

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Token, TokenAdmin)
