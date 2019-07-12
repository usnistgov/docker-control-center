from subprocess import CalledProcessError

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from docker.errors import NotFound
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import (
    APIException,
    NotFound as RestNotFound,
    PermissionDenied as RestPermissionDenied,
    ValidationError as RestValidationError,
)
from rest_framework.response import Response

from control_center.apps.api.serializers import ComposeProjectConfigSerializer, ComposeFileSerializer
from control_center.apps.delegate import docker
from control_center.apps.delegate.objects import ComposeProjectConfig
from control_center.libs.decorators.view_decorators import view_has_perm_from_arg


def unauthorized_function():
    raise RestPermissionDenied()


@api_view(["GET"])
def compose_config(request):
    config: ComposeProjectConfig = docker.compose_config()
    serializer = ComposeProjectConfigSerializer(config)
    return Response(serializer.data)


@api_view(["POST"])
@view_has_perm_from_arg("project_name", "up", unauthorized_function)
def project_up(request, project_name):
    try:
        docker.project_up(project_name)
        return Response({f"project '{project_name}' is up"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("project_name", "down", unauthorized_function)
def project_down(request, project_name):
    try:
        docker.project_down(project_name)
        return Response({f"project '{project_name}' is down"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("project_name", "restart", unauthorized_function)
def project_restart(request, project_name):
    try:
        docker.project_restart(project_name)
        return Response({f"project '{project_name}' has been restarted"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("project_name", "remove", unauthorized_function)
def project_remove(request, project_name):
    try:
        docker.project_remove(project_name)
        return Response({f"stopped containers for project '{project_name}' have been removed"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "start", unauthorized_function)
def service_start(request, project_name, service_name):
    try:
        docker.service_start(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' has been started"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "stop", unauthorized_function)
def service_stop(request, project_name, service_name):
    try:
        docker.service_stop(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' has been stopped"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "up", unauthorized_function)
def service_up(request, project_name, service_name):
    try:
        docker.service_up(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' is up"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "restart", unauthorized_function)
def service_restart(request, project_name, service_name):
    try:
        docker.service_restart(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' has been restarted"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "remove", unauthorized_function)
def service_remove(request, project_name, service_name):
    try:
        docker.service_remove(project_name, service_name)
        return Response(
            {f"stopped containers for service '{service_name}' of project '{project_name}' have been removed"}
        )
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "update", unauthorized_function)
def service_update(request, project_name, service_name):
    try:
        docker.service_update(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' has been updated"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["POST"])
@view_has_perm_from_arg("service_name", "rollback", unauthorized_function)
def service_rollback(request, project_name, service_name):
    try:
        docker.service_rollback(project_name, service_name)
        return Response({f"service '{service_name}' for project '{project_name}' has been rolled back"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["GET"])
@view_has_perm_from_arg("service_name", "logs", unauthorized_function)
def service_logs(request, project_name, service_name):
    lines = request.GET.get("lines", 100)
    try:
        logs = docker.service_logs(project_name, service_name, lines=lines, array=True)
        return Response({"lines": lines, "logs": logs, "project_name": project_name, "service_name": service_name})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)


@api_view(["GET"])
def service_logo(request, project_name, service_name):
    logo = docker.service_logo(project_name, service_name)
    if logo is None:
        return HttpResponse()
    return HttpResponse(logo)


@api_view(["POST"])
def container_stop(request, container_id):
    try:
        container = docker.container_stop(user=request.user, container_id=container_id)
        return Response({f"container '{container.name}' has been stopped"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)
    except CalledProcessError:
        raise APIException(detail="error stopping container")


@api_view(["POST"])
def container_start(request, container_id):
    try:
        container = docker.container_start(user=request.user, container_id=container_id)
        return Response({f"container '{container.name}' has been started"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)
    except CalledProcessError:
        raise APIException(detail="error starting container")


@api_view(["POST"])
def container_restart(request, container_id):
    try:
        container = docker.container_restart(user=request.user, container_id=container_id)
        return Response({f"container '{container.name}' has been restarted"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)
    except CalledProcessError:
        raise APIException(detail="error restarting container")


@api_view(["POST"])
def container_remove(request, container_id):
    try:
        container = docker.container_remove(user=request.user, container_id=container_id)
        return Response({f"container '{container.name}' has been removed"})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)
    except CalledProcessError:
        raise APIException(detail="error removing container")


@api_view(["GET"])
def container_logs(request, container_id):
    try:
        container = docker.container_by_id(container_id)
        docker.check_container_permission(user=request.user, container=container, perm="container_logs")
        lines = int(request.GET.get("lines", 100))
        logs = container.logs(lines=lines, array=True)
        return Response({"lines": lines, "logs": logs, "container_name": container.name, "container_id": container_id})
    except NotFound as error:
        raise RestNotFound(detail=error.explanation)
    except CalledProcessError:
        raise APIException(detail="error getting container logs")


@api_view(["POST"])
@permission_required("docker_system.system_commands", raise_exception=True)
def clean_old_images(request):
    docker.clean_old_images()
    return Response({"old images have been removed"})


@api_view(["POST"])
@permission_required("docker_system.system_commands", raise_exception=True)
def prune(request):
    docker.prune()
    return Response({"containers, networks and dangling images have been removed"})


@api_view(["POST"])
@permission_required("docker_system.system_commands", raise_exception=True)
def prune_all(request):
    docker.prune_all()
    return Response({"containers, networks, volumes and images have been removed"})


@api_view(["GET", "PUT"])
@permission_required("docker_system.system_commands", raise_exception=True)
def compose_file(request):
    if request.method == "GET":
        config = docker.compose_config()
        serializer = ComposeFileSerializer(
            {
                "path": config.compose_file_path,
                "project_name": config.project_name,
                "file_content": config.original_file_content(),
            }
        )
        return Response(serializer.data)
    if request.method == "PUT":
        serializer = ComposeFileSerializer(data=request.data)
        if serializer.is_valid():
            file_content = serializer.validated_data["file_content"]
            if file_content:
                try:
                    docker.update_compose_file_content(file_content=file_content)
                except ValidationError as error:
                    raise RestValidationError(detail=error.message)
                except Exception:
                    raise APIException()
        else:
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
