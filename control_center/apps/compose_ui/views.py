from subprocess import CalledProcessError

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseServerError, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from docker.errors import NotFound

from control_center.apps.compose_ui import docker
from control_center.apps.compose_ui.context import context
from control_center.apps.compose_ui.decorators import view_has_perm_from_arg, view_check_errors_redirect
from control_center.apps.compose_ui.objects import ComposeProject, ComposeService, Container


@login_required
def managed_containers(request):
    compose_config = docker.compose_config()
    ctx = context()
    if compose_config:
        ctx = context(
            {
                "project_list": docker.project_list(
                    docker.containers_for_project(compose_config.project_name), config=compose_config
                )
            }
        )
    return render(request, "compose_ui/project_containers.html", ctx)


@login_required
def other_project_containers(request):
    compose_config = docker.compose_config()
    ctx = context()
    if compose_config:
        ctx = context(
            {
                "project_list": docker.project_list(
                    docker.containers_for_project(exclude_project_name=compose_config.project_name)
                )
            }
        )
    return render(request, "compose_ui/project_containers.html", ctx)


@login_required
def standalone_containers(request):
    ctx = context({"container_list": docker.standalone_containers()})
    return render(request, "compose_ui/standalone_containers.html", ctx)


@login_required
def docker_system(request):
    config = docker.compose_config()
    return render(request, "compose_ui/system.html", context({"compose_file": bool(config)}))


@login_required
@view_has_perm_from_arg("project_name", "up")
@view_check_errors_redirect("error project up", lock=True)
def project_up(request, project_name):
    project = ComposeProject(project_name=project_name)
    project.up()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "down")
@view_check_errors_redirect("error project down", lock=True)
def project_down(request, project_name):
    project = ComposeProject(project_name=project_name)
    project.down()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "restart")
@view_check_errors_redirect("error restarting project", lock=True)
def project_restart(request, project_name):
    project = ComposeProject(project_name=project_name)
    project.restart()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("project_name", "remove")
@view_check_errors_redirect("error removing stopped containers for project", lock=True)
def project_rm(request, project_name):
    project = ComposeProject(project_name=project_name)
    project.rm()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "stop")
@view_check_errors_redirect("error stopping service", lock=True)
def service_stop(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.stop()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "start")
@view_check_errors_redirect("error starting service", lock=True)
def service_start(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.start()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "up")
@view_check_errors_redirect("error service up", lock=True)
def service_up(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.up()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "remove")
@view_check_errors_redirect("error removing stopped containers for service", lock=True)
def service_remove(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.rm()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "restart")
@view_check_errors_redirect("error restarting service", lock=True)
def service_restart(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.restart()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "update")
@view_check_errors_redirect("error updating service", lock=True)
def service_update(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.update()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "rollback")
@view_check_errors_redirect("error service rollback", lock=True)
def service_rollback(request, project_name, service_name):
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    service.rollback()
    return redirect_to_referer(request)


@login_required
@view_has_perm_from_arg("service_name", "logs")
@view_check_errors_redirect("error getting service logs")
def service_logs(request, project_name, service_name):
    lines = request.GET.get("lines", 100)
    service = ComposeService(
        project_name=project_name,
        service_name=service_name,
        service_config=docker.compose_config().service_config(project_name=project_name, service_name=service_name),
    )
    logs = service.logs(lines)
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
        container = docker.container_by_id(container_id)
        check_permission_or_deny(user=request.user, container=container, perm="container_stop")
        container.stop()
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
        container = docker.container_by_id(container_id)
        check_permission_or_deny(user=request.user, container=container, perm="container_start")
        container.start()
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
        container = docker.container_by_id(container_id)
        check_permission_or_deny(user=request.user, container=container, perm="container_restart")
        container.restart()
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
        container = docker.container_by_id(container_id)
        check_permission_or_deny(user=request.user, container=container, perm="container_remove")
        container.rm()
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
        check_permission_or_deny(user=request.user, container=container, perm="container_logs")
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
        return HttpResponseServerError("error removing container")
    except PermissionDenied:
        return HttpResponseForbidden()


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error removing dangling images", lock=True)
def clean_old_images(request):
    images = docker.client().images.list(all=True, filters={"dangling": True})

    for image in images:
        docker.client().images.remove(image.id, force=True)
    return redirect_to_referer(request)


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error with docker system prune", lock=True)
def prune(request):
    clean_old_images(request)
    client = docker.client()
    client.containers.prune()
    client.networks.prune()
    return redirect_to_referer(request)


@login_required()
@permission_required("docker_system.system_commands", raise_exception=True)
@view_check_errors_redirect("error with docker system prune all", lock=True)
def prune_all(request):
    prune(request)
    client = docker.client()
    client.images.prune()
    client.volumes.prune()
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
    compose_config = docker.compose_config()
    file_content: str = request.POST["file_content"]
    if file_content:
        original_file_content = open(compose_config.compose_file_path, "r").read()
        file_content = file_content.replace("\r\n", "\n")
        open(compose_config.compose_file_path, "w").write(file_content)
        error = docker.validate_and_resolve_config(raise_error=False)
        if error:
            open(compose_config.compose_file_path, "w").write(original_file_content)
            return view_compose_file(request, error=error)
        else:
            return managed_containers(request)


# Checks whether a user has permission to perform the action on a container; if not, raise PermissionDenied
def check_permission_or_deny(user: User, container: Container, perm: str):
    compose_config = docker.compose_config()
    app_label = None
    if container.project and container.project == compose_config.project_name:
        app_label = container.service
    elif container.project and container.project != compose_config.project_name:
        app_label = "other_projects"
    elif not container.project:
        app_label = "other_containers"
    if not user.has_perm(app_label + "." + perm):
        raise PermissionDenied


def redirect_to_referer(request):
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
