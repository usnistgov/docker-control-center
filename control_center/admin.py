from django.conf import settings

from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy


class MyAdminSite(AdminSite):
    site_header = ugettext_lazy(settings.SITE_TITLE)
    site_title = ugettext_lazy(settings.SITE_TITLE)
    index_title = ugettext_lazy("Detailed administration")


admin_site = MyAdminSite()

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
