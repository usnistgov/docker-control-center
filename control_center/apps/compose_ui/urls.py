from django.urls import path

from control_center.apps.compose_ui import views

urlpatterns = [
    path("managed_containers", views.managed_containers, name="managed_containers"),
    path("other_project_containers", views.other_project_containers, name="other_project_containers"),
    path("standalone_containers", views.standalone_containers, name="standalone_containers"),
    path("docker_system", views.docker_system, name="docker_system"),
    # docker compose project commands
    path("project/<str:project_name>/up", views.project_up, name="project_up"),
    path("project/<str:project_name>/down", views.project_down, name="project_down"),
    path("project/<str:project_name>/restart", views.project_restart, name="project_restart"),
    path("project/<str:project_name>/rm", views.project_rm, name="project_remove"),
    # docker compose service commands
    path("project/<str:project_name>/service/<str:service_name>/stop", views.service_stop, name="service_stop"),
    path("project/<str:project_name>/service/<str:service_name>/start", views.service_start, name="service_start"),
    path("project/<str:project_name>/service/<str:service_name>/up", views.service_up, name="service_up"),
    path(
        "project/<str:project_name>/service/<str:service_name>/restart", views.service_restart, name="service_restart"
    ),
    path("project/<str:project_name>/service/<str:service_name>/rm", views.service_remove, name="service_remove"),
    path("project/<str:project_name>/service/<str:service_name>/update", views.service_update, name="service_update"),
    path(
        "project/<str:project_name>/service/<str:service_name>/rollback",
        views.service_rollback,
        name="service_rollback",
    ),
    path("project/<str:project_name>/service/<str:service_name>/logs", views.service_logs, name="service_logs"),
    # container functions
    path("container/<str:container_id>/stop", views.container_stop, name="container_stop"),
    path("container/<str:container_id>/start", views.container_start, name="container_start"),
    path("container/<str:container_id>/restart", views.container_restart, name="container_restart"),
    path("container/<str:container_id>/rm", views.container_remove, name="container_remove"),
    path("container/<str:container_id>/logs", views.container_logs, name="container_logs"),
    # docker system commands
    path("system/view_compose_file", views.view_compose_file, name="view_compose_file"),
    path("system/edit_compose_file", views.edit_compose_file, name="system_edit_compose_file"),
    path("system/clean_old_images", views.clean_old_images, name="system_clean_old_images"),
    path("system/prune", views.prune, name="system_prune"),
    path("system/prune_all", views.prune_all, name="system_prune_all"),
]
