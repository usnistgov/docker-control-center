from subprocess import CalledProcessError

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseServerError, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from docker.errors import NotFound

from control_center.apps.compose_ui.context import context
from control_center.apps.compose_ui.decorators import view_check_errors_redirect
from control_center.apps.delegate import docker
from control_center.libs.decorators.view_decorators import view_has_perm_from_arg


def unauthorized_function():
    return HttpResponseForbidden  # 403 Forbidden is better than 404


@login_required
def managed_containers(request):
    ctx = context()
    project_name = docker.compose_config().project_name if docker.compose_config() else None
    if project_name:
        ctx = context({"project_list": [docker.compose_project_by_name(docker.compose_config().project_name)]})
    return render(request, "compose_ui/project_containers.html", ctx)


@login_required
def other_project_containers(request):
    ctx = context()
    project_name_to_exclude = docker.compose_config().project_name if docker.compose_config() else None
    if project_name_to_exclude:
        ctx = context(
            {
                "container_list": docker.containers_for_project(exclude_project_name=project_name_to_exclude),
                "other_projects": True,
            }
        )
    return render(request, "compose_ui/standalone_containers.html", ctx)


@login_required
def standalone_containers(request):
    ctx = context({"container_list": docker.standalone_containers()})
    return render(request, "compose_ui/standalone_containers.html", ctx)


@login_required
def docker_system(request):
    config = docker.compose_config()
    return render(request, "compose_ui/system.html", context({"compose_file": bool(config)}))


@login_required
@view_has_perm_from_arg("project_name", "up", unauthorized_function)
@view_check_errors_redirect("error project up", lock=True)
def project_up(request, project_name):
    docker.project_up(project_name=project_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "down", unauthorized_function)
@view_check_errors_redirect("error project down", lock=True)
def project_down(request, project_name):
    docker.project_down(project_name=project_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "restart", unauthorized_function)
@view_check_errors_redirect("error restarting project", lock=True)
def project_restart(request, project_name):
    docker.project_restart(project_name=project_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "remove", unauthorized_function)
@view_check_errors_redirect("error removing stopped containers for project", lock=True)
def project_rm(request, project_name):
    docker.project_remove(project_name=project_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "stop", unauthorized_function)
@view_check_errors_redirect("error stopping service", lock=True)
def service_stop(request, project_name, service_name):
    docker.service_stop(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "start", unauthorized_function)
@view_check_errors_redirect("error starting service", lock=True)
def service_start(request, project_name: str, service_name: str):
    docker.service_start(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "up", unauthorized_function)
@view_check_errors_redirect("error service up", lock=True)
def service_up(request, project_name, service_name):
    docker.service_up(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "remove", unauthorized_function)
@view_check_errors_redirect("error removing stopped containers for service", lock=True)
def service_remove(request, project_name, service_name):
    docker.service_remove(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "restart", unauthorized_function)
@view_check_errors_redirect("error restarting service", lock=True)
def service_restart(request, project_name, service_name):
    docker.service_restart(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "update", unauthorized_function)
@view_check_errors_redirect("error updating service", lock=True)
def service_update(request, project_name, service_name):
    docker.service_update(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "rollback", unauthorized_function)
@view_check_errors_redirect("error service rollback", lock=True)
def service_rollback(request, project_name, service_name):
    docker.service_rollback(project_name=project_name, service_name=service_name)
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "logs", unauthorized_function)
@view_check_errors_redirect("error getting service logs")
def service_logs(request, project_name, service_name):
    lines = request.GET.get("lines", 100)
    logs = docker.service_logs(project_name=project_name, service_name=service_name, lines=lines)
    return render(
        request,
        "compose_ui/logs.html",
        context(
            {
                "auto_refresh": False,  # never auto-refresh logs
                "lines": lines,
                "project_name": project_name,
                "service_name": service_name,
                "logs": logs,
            }
        ),
    )


@login_required
def container_stop(request, container_id):
    try:
        docker.container_stop(user=request.user, container_id=container_id)
    except NotFound as error:
        raise Http404(error.explanation)
    except CalledProcessError:
        return HttpResponseServerError("error stopping container")
    except PermissionDenied:
        return HttpResponseForbidden()
    return redirect_to_referer(request)


@login_required
def container_start(request, container_id):
    try:
        docker.container_start(user=request.user, container_id=container_id)
    except NotFound as error:
        raise Http404(error.explanation)
    except CalledProcessError:
        return HttpResponseServerError("error starting container")
    except PermissionDenied:
        return HttpResponseForbidden()
    return redirect_to_referer(request)


@login_required
def container_restart(request, container_id):
    try:
        docker.container_restart(user=request.user, container_id=container_id)
    except NotFound as error:
        raise Http404(error.explanation)
    except CalledProcessError:
        return HttpResponseServerError("error restarting container")
    except PermissionDenied:
        return HttpResponseForbidden()
    return redirect_to_referer(request)


@login_required
def container_remove(request, container_id):
    try:
        docker.container_remove(user=request.user, container_id=container_id)
    except NotFound as error:
        raise Http404(error.explanation)
    except CalledProcessError:
        return HttpResponseServerError("error removing container")
    except PermissionDenied:
        return HttpResponseForbidden()
    return redirect_to_referer(request)


@login_required
def container_logs(request, container_id):
    try:
        container = docker.container_by_id(container_id)
        docker.check_container_permission(user=request.user, container=container, perm="container_logs")
        lines = int(request.GET.get("lines", 100))
        logs = container.logs(lines)
        return render(
            request,
            "compose_ui/logs.html",
            context(
                {
                    "auto_refresh": False,  # never auto-refresh logs
                    "lines": lines,
                    "container_name": container.name,
                    "logs": logs,
                }
            ),
        )
    except NotFound as error:
        raise Http404(error.explanation)
    except CalledProcessError:
        return HttpResponseServerError("error getting container logs")
    except PermissionDenied:
        return HttpResponseForbidden()


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error removing dangling images", lock=True)
def clean_old_images(request):
    docker.clean_old_images()
    return redirect_to_referer(request)


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error with docker system prune", lock=True)
def prune(request):
    docker.prune()
    return redirect_to_referer(request)


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error with docker system prune all", lock=True)
def prune_all(request):
    docker.prune_all()
    return redirect_to_referer(request)


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error with reading compose file", lock=True)
def view_compose_file(request, error=None):
    compose_config = docker.compose_config()
    return render(
        request,
        "compose_ui/file_editor.html",
        context({"doc_file": compose_config.original_file_content(), "error": error}),
    )


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
def edit_compose_file(request):
    file_content: str = request.POST["file_content"]
    if file_content:
        try:
            docker.update_compose_file_content(file_content=file_content)
        except ValidationError as error:
            return view_compose_file(request, error=error.message)
        else:
            return managed_containers(request)


def redirect_to_referer(request):
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
