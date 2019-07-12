from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

from control_center.apps.api import views

urlpatterns = [
    path("token-auth/", rest_framework_views.obtain_auth_token),
    path("compose_config/", views.compose_config),
    # docker compose project commands
    path("project/<str:project_name>/up", views.project_up),
    path("project/<str:project_name>/down", views.project_down),
    path("project/<str:project_name>/restart", views.project_restart),
    path("project/<str:project_name>/rm", views.project_remove),
    # docker compose service commands
    path("project/<str:project_name>/service/<str:service_name>/stop", views.service_stop),
    path("project/<str:project_name>/service/<str:service_name>/start", views.service_start),
    path("project/<str:project_name>/service/<str:service_name>/up", views.service_up),
    path("project/<str:project_name>/service/<str:service_name>/restart", views.service_restart),
    path("project/<str:project_name>/service/<str:service_name>/rm", views.service_remove),
    path("project/<str:project_name>/service/<str:service_name>/update", views.service_update),
    path("project/<str:project_name>/service/<str:service_name>/rollback", views.service_rollback),
    path("project/<str:project_name>/service/<str:service_name>/logs", views.service_logs),
    path("project/<str:project_name>/service/<str:service_name>/logo", views.service_logo, name="service_logo"),
    # container functions
    path("container/<str:container_id>/stop", views.container_stop),
    path("container/<str:container_id>/start", views.container_start),
    path("container/<str:container_id>/restart", views.container_restart),
    path("container/<str:container_id>/rm", views.container_remove),
    path("container/<str:container_id>/logs", views.container_logs),
    # docker system commands
    path("system/compose_file", views.compose_file),
    path("system/clean_old_images", views.clean_old_images),
    path("system/prune", views.prune),
    path("system/prune_all", views.prune_all),
]
