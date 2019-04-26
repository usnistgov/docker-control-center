import os
import subprocess
from logging import getLogger
from subprocess import CalledProcessError
from typing import List, Dict

import docker
import yaml
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from docker import DockerClient

from control_center.apps.compose_ui.objects import ComposeService, ComposeProjectConfig, Container, ComposeProject

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
                    _cache["config"] = ComposeProjectConfig(
                        compose_file_path=settings.YML_PATH, config=yml_file, project_name=settings.COMPOSE_PROJECT
                    )
                    create_permissions_for_config(_cache["config"])
                    Permission.objects.all()
                    logger.debug("success")
            except IOError as io_err:
                logger.exception("error opening file", io_err)
                raise SystemExit(f"error loading file {settings.YML_PATH}")
            except yaml.YAMLError as exc:
                logger.exception("error loading file", exc)
                raise SystemExit("error loading file")
        return _cache["config"]


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


def validate_and_resolve_config(raise_error=True) -> [str, str]:
    try:
        return execute_compose_command(settings.COMPOSE_PROJECT, ["config"], debug=False)
    except CalledProcessError as error:
        if raise_error:
            raise SystemExit(error.output.decode())
        else:
            return error.output.decode()


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
    for container in docker_container_list:
        container_dto = Container(container=container)
        if project_name and container_dto.project == project_name:
            container_list.append(container_dto)
        if exclude_project_name and container_dto.project != exclude_project_name:
            container_list.append(container_dto)
    return container_list


def standalone_containers() -> List[Container]:
    container_list = []
    docker_container_list = client().containers.list(all=True)
    for container in docker_container_list:
        container_dto = Container(container=container)
        if not container_dto.project and not container_dto.service:
            container_list.append(container_dto)
    return container_list


def containers_for_service(project_name, service_name) -> List[Container]:
    container_dto_list = []
    for container in client().containers.list(
        all=True,
        filters={"label": [f"com.docker.compose.service={service_name}", f"com.docker.compose.project={project_name}"]},
    ):
        container_dto = Container(container=container)
        container_dto_list.append(container_dto)
    return container_dto_list


def container_by_id(container_id) -> Container:
    return Container(client().containers.get(container_id=container_id))


def project_list(container_list: List[Container], config: ComposeProjectConfig = None):
    projects: List[ComposeProject] = []
    if config:
        project = ComposeProject(project_name=config.project_name, project_config=config)
        for service_conf in config.service_configs:
            project.services.append(
                ComposeService(
                    project_name=project.project_name,
                    service_name=service_conf.service_name,
                    service_config=service_conf,
                )
            )
        projects.append(project)

    for container in container_list:
        if container.project and container.service:
            if not list(filter(lambda prj: prj.project_name == container.project, projects)):
                projects.append(ComposeProject(project_name=container.project))
            project = next(filter(lambda prj: prj.project_name == container.project, projects))
            if not list(filter(lambda ser: ser.service_name == container.service, project.services)):
                project.services.append(
                    ComposeService(service_name=container.service, project_name=container.project, service_config=None)
                )
    return projects


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
