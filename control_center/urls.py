from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.views.generic import RedirectView

from control_center.admin import admin_site

admin_site.login = login_required(admin_site.login)

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="managed_containers", permanent=False)
        if settings.YML_PATH
        else RedirectView.as_view(pattern_name="standalone_containers", permanent=False),
        name="index",
    ),
    # Admin pages
    path("admin/", admin_site.urls),
    # Docker Compose UI pages
    path("docker/", include("control_center.apps.compose_ui.urls")),
    # Authentication pages:
    path("auth/", include("control_center.libs.authentication.urls")),
]
