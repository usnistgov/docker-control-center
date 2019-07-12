import configparser
import os
import subprocess
from configparser import ConfigParser
from logging import getLogger
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Dict

import docker
import yaml
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from docker import DockerClient
from docker.errors import NotFound

from control_center.apps.delegate.objects import (
    ComposeService,
    ComposeProjectConfig,
    Container,
    ComposeProject,
    ComposeServiceConfig,
)

logger = getLogger("control_center")

_cache: Dict = {"last_modified": 0, "config": None}

if hasattr(settings, "PRIVATE_DOCKER_REPOSITORY") and settings.PRIVATE_DOCKER_REPOSITORY["available"]:
    logger.debug(f"docker login to {settings.PRIVATE_DOCKER_REPOSITORY['url']}")
    subprocess.check_output(
        [
            "docker",
            "login",
            "--username",
            settings.PRIVATE_DOCKER_REPOSITORY["username"],
            "--password",
            settings.PRIVATE_DOCKER_REPOSITORY["password"],
            settings.PRIVATE_DOCKER_REPOSITORY["url"],
        ]
    )


def compose_config() -> ComposeProjectConfig:
    if settings.YML_PATH:
        if not os.path.exists(settings.YML_PATH):
            message = f"docker-compose file [{settings.YML_PATH}] not found"
            logger.exception(message)
            raise SystemExit(Exception(message))
        last_modified = os.path.getmtime(settings.YML_PATH)
        if last_modified > _cache.get("last_modified", 0):
            yml_config = validate_and_resolve_config()
            _cache["last_modified"] = last_modified
            try:
                logger.debug(f"loading yml file at {settings.YML_PATH}")
                yml_file = yaml.load(yml_config, Loader=yaml.Loader)
                if yml_file:
                    project_config = ComposeProjectConfig(
                        compose_file_path=settings.YML_PATH,
                        config=yml_file,
                        extra_config=get_extra_config_file(settings.EXTRA_COMPOSE_CONFIG),
                        project_name=settings.COMPOSE_PROJECT,
                    )
                    _cache["config"] = project_config
                    create_permissions_for_config(_cache["config"])
            except yaml.YAMLError as exc:
                logger.exception("error loading file", exc)
                raise SystemExit("error loading file")
        return _cache["config"]


def get_extra_config_file(extra_path: str) -> ConfigParser:
    config = configparser.ConfigParser()
    config.read(extra_path)
    return config


def create_permissions_for_config(config: ComposeProjectConfig):
    other_projects_app_label = "other_projects"
    other_containers_app_label = "other_containers"
    docker_system_app_label = "docker_system"
    project_permissions = ["up", "down", "remove", "restart"]
    service_permissions = ["view", "up", "stop", "start", "remove", "restart", "scale", "update", "rollback", "logs"]
    container_permissions = ["stop", "start", "remove", "restart", "rename", "logs"]
    project_content_type, created = ContentType.objects.get_or_create(app_label=config.project_name, model="projects")
    for perm in project_permissions:
        name = f"Can {perm} project"
        codename = perm
        if not any(Permission.objects.filter(content_type=project_content_type, codename=codename)):
            Permission.objects.create(content_type=project_content_type, name=name, codename=codename)
    for service in config.service_configs:
        service_content_type, created = ContentType.objects.get_or_create(
            app_label=service.service_name, model="services"
        )
        for perm in service_permissions:
            name = f"Can {perm} service" if perm != "logs" else "Can see service logs"
            codename = perm
            if not any(Permission.objects.filter(content_type=service_content_type, codename=codename)):
                Permission.objects.create(content_type=service_content_type, name=name, codename=codename)
        for perm in container_permissions:
            name = f"Can {perm} container"
            codename = "container_" + perm
            if not any(Permission.objects.filter(content_type=service_content_type, codename=codename)):
                Permission.objects.create(content_type=service_content_type, name=name, codename=codename)
    # Creates special set of permissions for other project containers and other containers
    other_projects_content_type, created = ContentType.objects.get_or_create(
        app_label=other_projects_app_label, model="other"
    )
    for perm in container_permissions:
        name = f"Can {perm} container"
        codename = "container_" + perm
        if not any(Permission.objects.filter(content_type=other_projects_content_type, codename=codename)):
            Permission.objects.create(content_type=other_projects_content_type, name=name, codename=codename)
    other_containers_content_type, created = ContentType.objects.get_or_create(
        app_label=other_containers_app_label, model="other"
    )
    for perm in container_permissions:
        name = f"Can {perm} container"
        codename = "container_" + perm
        if not any(Permission.objects.filter(content_type=other_containers_content_type, codename=codename)):
            Permission.objects.create(content_type=other_containers_content_type, name=name, codename=codename)
    system_content_type, created = ContentType.objects.get_or_create(app_label=docker_system_app_label, model="docker")
    name = "Can use docker system commands"
    codename = "system_commands"
    if not any(Permission.objects.filter(content_type=system_content_type, codename=codename)):
        Permission.objects.create(content_type=system_content_type, name=name, codename=codename)


def validate_and_resolve_config(raise_error=False) -> [str, str]:
    try:
        return execute_compose_command(settings.COMPOSE_PROJECT, ["config"], debug=False)
    except CalledProcessError as error:
        if not raise_error:
            raise SystemExit(error.output.decode())
        else:
            raise error


def service_hashes(project_name: str) -> Dict:
    hashes = execute_compose_command(project_name=project_name, args=["config", "--hash=*"])
    if hashes:
        return {project_name: dict(line.split(" ") for line in hashes.splitlines())}


def client() -> DockerClient:
    docker_client = docker.from_env()
    return docker_client


def pull_image(project_name, service_name):
    logger.debug(f"pulling image for {service_name}")
    execute_compose_command(project_name=project_name, args=["pull", service_name])


def containers_for_project(project_name: str = None, exclude_project_name: str = None) -> List[Container]:
    container_list = []
    docker_container_list = client().containers.list(all=True, filters={"label": "com.docker.compose.project"})
    for docker_container in docker_container_list:
        container = Container(container=docker_container)
        if project_name and container.project == project_name:
            container_list.append(container)
        if exclude_project_name and container.project != exclude_project_name:
            container_list.append(container)
    return container_list


def standalone_containers() -> List[Container]:
    container_list = []
    docker_container_list = client().containers.list(all=True)
    for docker_container in docker_container_list:
        container = Container(container=docker_container)
        if not container.project and not container.service:
            container_list.append(container)
    return container_list


def containers_for_service(project_name, service_name) -> List[Container]:
    container_list = []
    for docker_container in client().containers.list(
        all=True,
        filters={"label": [f"com.docker.compose.service={service_name}", f"com.docker.compose.project={project_name}"]},
    ):
        container = Container(container=docker_container)
        container_list.append(container)
    return container_list


def container_by_id(container_id) -> Container:
    return Container(client().containers.get(container_id=container_id))


def compose_service(project_name: str, service_name: str) -> ComposeService:
    try:
        service_config: ComposeServiceConfig = compose_config().get_service_config(
            project_name=project_name, service_name=service_name
        )
        return ComposeService(project_name=project_name, service_name=service_name, service_config=service_config)
    except StopIteration:
        message = f"couldn't find service '{service_name}' in project '{project_name}'"
        raise NotFound(message="Not Found", explanation=message)


def compose_project_by_name(project_name: str) -> ComposeProject:
    project_config: ComposeProjectConfig = compose_config()
    if project_config.project_name == project_name:
        return ComposeProject(project_name=project_name, project_config=project_config)
    else:
        message = f"couldn't find project '{project_name}'"
        raise NotFound(message="Not Found", explanation=message)


def execute_compose_command(project_name: str, args: List[str], debug: bool = True) -> str:
    try:
        arguments = []
        if settings.WINDOWS_HOST:
            arguments = ["env", "COMPOSE_FORCE_WINDOWS_HOST=1", "env", "COMPOSE_CONVERT_WINDOWS_PATHS=1"]
        arguments = arguments + ["docker-compose", "--log-level", "ERROR"]
        if settings.COMPATIBILITY_MODE:
            arguments = arguments + ["--compatibility"]
        arguments = arguments + ["--file", settings.YML_PATH, "--project-name", project_name] + args
        if debug:
            logger.debug("command:\n" + str(arguments))
        output = subprocess.check_output(arguments, stderr=subprocess.STDOUT).decode()
        if debug:
            logger.debug("output:\n" + output)
        return output
    except CalledProcessError as error:
        error_output = error.output.decode()
        logger.exception(f"error running docker-compose command: {error_output}")
        raise error


# Checks whether a user has permission to perform the action on a container; if not, raise PermissionDenied
def check_container_permission(user: User, container: Container, perm: str):
    config = compose_config()
    app_label = None
    if container.project and container.project == config.project_name:
        app_label = container.service
    elif container.project and container.project != config.project_name:
        app_label = "other_projects"
    elif not container.project:
        app_label = "other_containers"
    if not user.has_perm(app_label + "." + perm):
        raise PermissionDenied


def update_compose_file_content(file_content: str):
    config = compose_config()
    original_file_content = open(config.compose_file_path, "r").read()
    file_content = file_content.replace("\r\n", "\n")
    try:
        open(config.compose_file_path, "w").write(file_content)
        validate_and_resolve_config(raise_error=True)
    except CalledProcessError as error:
        open(config.compose_file_path, "w").write(original_file_content)
        raise ValidationError(message=error.output.decode())
    except Exception as err:
        open(config.compose_file_path, "w").write(original_file_content)
        raise err


def project_up(project_name: str):
    project = compose_project_by_name(project_name=project_name)
    project.up()


def project_down(project_name: str):
    project = compose_project_by_name(project_name=project_name)
    project.down()


def project_remove(project_name: str):
    project = compose_project_by_name(project_name=project_name)
    project.rm()


def project_restart(project_name: str):
    project = compose_project_by_name(project_name=project_name)
    project.restart()


def service_up(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.up()


def service_stop(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.stop()


def service_start(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.start()


def service_remove(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.rm()


def service_restart(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.restart()


def service_scale(project_name: str, service_name: str, scale: int):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.scale(scale)


def service_update(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.update()


def service_rollback(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    service.rollback()


def service_logs(project_name: str, service_name: str, lines: int = 100, array=False) -> str:
    service = compose_service(project_name=project_name, service_name=service_name)
    return service.logs(lines=lines, array=array)


def service_logo(project_name: str, service_name: str):
    service = compose_service(project_name=project_name, service_name=service_name)
    if service.config.logo:
        return get_logo_file(os.path.join(Path(settings.EXTRA_COMPOSE_CONFIG).parent, service.config.logo))


def get_logo_file(path):
    logo = None
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            logo = f.read()
    return logo


def container_stop(user: User, container_id: str):
    container = container_by_id(container_id)
    check_container_permission(user=user, container=container, perm="container_remove")
    container.stop()
    return container


def container_start(user: User, container_id: str):
    container = container_by_id(container_id)
    check_container_permission(user=user, container=container, perm="container_remove")
    container.start()
    return container


def container_restart(user: User, container_id: str):
    container = container_by_id(container_id)
    check_container_permission(user=user, container=container, perm="container_remove")
    container.restart()
    return container


def container_remove(user: User, container_id: str):
    container = container_by_id(container_id)
    check_container_permission(user=user, container=container, perm="container_remove")
    container.rm()
    return container


def clean_old_images():
    images = client().images.list(all=True, filters={"dangling": True})
    for image in images:
        client().images.remove(image.id, force=True)


def prune():
    clean_old_images()
    client().containers.prune()
    client().networks.prune()


def prune_all():
    prune()
    client().images.prune()
    client().volumes.prune()
