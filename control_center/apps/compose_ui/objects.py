from datetime import datetime
from types import SimpleNamespace
from typing import List, Optional

from dateutil import parser
from django.conf import settings
from django.utils.dateparse import parse_datetime
from docker.errors import ImageNotFound
from docker.models.containers import Container as DockerContainer
from pytz import utc

from control_center.apps.compose_ui import docker


class ComposeServiceConfig(object):
    def __init__(self, config: dict, service_name: str, service_hash: str):
        self._config: dict = config
        self.service_name: str = service_name
        self.hash = service_hash
        self.image: str = config.get("image")
        self.container_name: str = config.get("container_name")
        self.restart: str = config.get("restart")
        self.scale: int = self.get_scale(config)
        self.volumes: List[str] = config.get("volumes")
        self.ports: List[str] = config.get("ports")
        self.environment: dict = config.get("environment")
        self.depends_on: List[str] = config.get("depends_on")
        self.links: List[str] = config.get("links")

    def merged_dependencies(self) -> List[str]:
        return list(set(self.depends_on) | set(self.links))

    @staticmethod
    def get_scale(config: dict) -> int:
        if config:
            if "scale" in config.keys():
                return config["scale"]
        return 1


class ComposeProjectConfig(object):
    def __init__(self, compose_file_path, config: dict, project_name: str):
        self._config: object = config
        self.compose_file_path = compose_file_path
        self.project_name: str = project_name
        self.version: float = float(config["version"])
        service_hash_dict = docker.service_hashes(project_name=project_name)
        self.service_configs: List[ComposeServiceConfig] = []
        for service_name in config["services"]:
            self.service_configs.append(
                ComposeServiceConfig(
                    config=config["services"][service_name],
                    service_name=service_name,
                    service_hash=service_hash_dict[self.project_name][service_name],
                )
            )

    def original_file_content(self):
        with open(self.compose_file_path, "r") as stream:
            return stream.read()

    def service_config(self, project_name: str, service_name: str):
        if project_name == self.project_name:
            return next(filter(lambda ser_conf: ser_conf.service_name == service_name, self.service_configs))


class Container(object):
    STATUS = SimpleNamespace(
        **{
            "CREATED": "created",
            "RESTARTING": "restarting",
            "RUNNING": "running",
            "REMOVING": "removing",
            "PAUSED": "paused",
            "EXITED": "exited",
            "DEAD": "dead",
        }
    )

    def __init__(self, container: DockerContainer):
        self._docker_container: DockerContainer = container
        self.name: str = container.name
        self.short_id: str = container.short_id
        self.id: str = container.id
        try:
            self.tags: str = container.image.tags
        except ImageNotFound:
            self.tags = None
        self.status: str = container.status
        self.started_at: datetime = parse_datetime(container.attrs["State"]["StartedAt"]) if parse_datetime(
            container.attrs["State"]["StartedAt"]
        ) != utc.localize(datetime.min) else None
        self.service: str = container.labels.get("com.docker.compose.service")
        self.service_hash: str = container.labels.get("com.docker.compose.config-hash")
        self.project: str = container.labels.get("com.docker.compose.project")

    def tags_display(self) -> str:
        if self.tags:
            tags_joined = "\n".join(self.tags)
            return remove_custom_registry_from_image_name(tags_joined) if self.tags else tags_joined
        return ""

    def can_be_stopped(self) -> bool:
        return self.status == self.STATUS.RUNNING

    def can_be_started(self) -> bool:
        return self.status == self.STATUS.EXITED

    def can_be_restarted(self):
        return self.status == self.STATUS.RUNNING

    def can_be_removed(self):
        return self.status == self.STATUS.EXITED

    def stop(self):
        self._docker_container.stop()

    def start(self):
        self._docker_container.start()

    def restart(self):
        self._docker_container.restart()

    def rm(self):
        self._docker_container.remove()

    def rename(self, name: str):
        self._docker_container.rename(name)

    def logs(self, lines: int) -> str:
        output = self._docker_container.logs(tail=lines, timestamps=True)
        if output:
            output = output.decode()
            log_output = output.split("\n")
            new_output = [recompose_log_line_with_formatted_date(line, "%m-%d %H:%M:%S") for line in log_output]
            return "\n".join(new_output)


class ComposeService(object):
    ROLLBACK_SUFFIX = "_previous"

    def __init__(self, service_name: str, project_name: str, service_config: Optional[ComposeServiceConfig]):
        self.service_name: str = service_name
        self.project_name: str = project_name
        self.config: Optional[ComposeServiceConfig] = service_config
        self.containers: List[Container] = []
        self.refresh_containers()

    def refresh_containers(self):
        self.containers = docker.containers_for_service(project_name=self.project_name, service_name=self.service_name)

    def stopped_containers(self) -> List[Container]:
        return list(filter(lambda cont: cont.status == Container.STATUS.EXITED, self.containers))

    def running_containers(self) -> List[Container]:
        return list(filter(lambda cont: cont.status == Container.STATUS.RUNNING, self.containers))

    def rollback_containers(self) -> List[Container]:
        return list(filter(lambda cont: cont.name.endswith(self.ROLLBACK_SUFFIX), self.containers))

    def out_of_sync_containers(self) -> List[Container]:
        return list(filter(lambda cont: self.config and cont.service_hash != self.config.hash, self.containers))

    def config_image_display(self) -> str:
        return remove_custom_registry_from_image_name(self.config.image) if self.config else ""

    def can_be_upped(self) -> bool:
        return not any(self.rollback_containers())

    def can_be_started(self) -> bool:
        return not any(self.rollback_containers()) and any(self.stopped_containers())

    def can_be_stopped(self) -> bool:
        return any(self.running_containers())

    def can_be_restarted(self) -> bool:
        return not any(self.rollback_containers()) and any(self.containers)

    def can_be_removed(self) -> bool:
        return any(self.stopped_containers())

    def can_be_updated(self) -> bool:
        return (
            self.config
            and not self.config.ports
            and any(filter(lambda cont: cont not in self.rollback_containers(), self.out_of_sync_containers()))
        )

    def can_be_rolled_back(self) -> bool:
        return any(self.rollback_containers())

    def up(self):
        docker.pull_image(project_name=self.project_name, service_name=self.service_name)
        docker.execute_compose_command(self.project_name, ["up", "--detach", "--no-deps", self.service_name])

    def stop(self):
        docker.execute_compose_command(self.project_name, ["stop", self.service_name])

    def start(self):
        docker.execute_compose_command(self.project_name, ["start", self.service_name])

    def rm(self):
        docker.execute_compose_command(self.project_name, ["rm", "--force", self.service_name])

    def restart(self):
        docker.execute_compose_command(self.project_name, ["restart", self.service_name])

    def scale(self, scale):
        docker.pull_image(project_name=self.project_name, service_name=self.service_name)
        docker.execute_compose_command(
            self.project_name,
            [
                "up",
                "--detach",
                "--no-deps",
                "--scale",
                f"{self.service_name}={scale}",
                "--no-recreate",
                self.service_name,
            ],
        )

    def update(self):
        docker.pull_image(project_name=self.project_name, service_name=self.service_name)
        # remove previous rollback containers
        for container in self.rollback_containers():
            container.rm()
        self.refresh_containers()
        # rename current containers
        for container in self.containers:
            new_name = container.name + self.ROLLBACK_SUFFIX
            container.rename(new_name)
        self.refresh_containers()
        # scale
        self.scale(self.config.scale * 2)
        # stop old containers
        for container in self.rollback_containers():
            container.stop()
        # run extra command
        run_extra_command(self.project_name)

    def rollback(self):
        rollback_containers = self.rollback_containers()
        for container in self.containers:
            if container not in rollback_containers:
                container.stop()
                container.rm()
            elif container in rollback_containers:
                container.rename(container.name.replace(self.ROLLBACK_SUFFIX, ""))
                container.start()
        run_extra_command(self.project_name)

    def logs(self, lines=100) -> str:
        log_output = docker.execute_compose_command(
            self.project_name, ["logs", "--no-color", "--timestamps", f"--tail={lines}", self.service_name], debug=False
        )
        # remove first line of logs (it's useless)
        log_output = log_output.split("\n")[1:]

        new_output = [recompose_log_line_with_formatted_date(line, "%m-%d %H:%M:%S") for line in log_output]

        return "\n".join(new_output)


def recompose_log_line_with_formatted_date(line: str, date_format: str) -> str:
    new_line = line
    # docker-compose has a very strict formatting. date is always 31 long, after | character
    if line and "|" in line:
        index_date_start = line.index("|") + 1
        index_date_end = index_date_start + 31
        date = parser.parse(line[index_date_start:index_date_end])
        new_line = line[0 : index_date_start + 1] + date.strftime(date_format) + line[index_date_end : len(line)]
    return new_line


def run_extra_command(project_name: str):
    if getattr(settings, "EXTRA_DOCKER_COMPOSE_COMMAND"):
        docker.execute_compose_command(project_name=project_name, args=settings.EXTRA_DOCKER_COMPOSE_COMMAND)


class ComposeProject(object):
    def __init__(
        self, project_name: str, project_config: ComposeProjectConfig = None, services: List[ComposeService] = None
    ):
        self.project_name: str = project_name
        self.config: ComposeProjectConfig = project_config
        self.services: List[ComposeService] = [] if services is None else services

    def stopped_containers(self) -> List[Container]:
        return [container for sublist in self.services for container in sublist.stopped_containers()]

    def running_containers(self) -> List[Container]:
        return [container for sublist in self.services for container in sublist.running_containers()]

    def rollback_containers(self) -> List[Container]:
        return [container for sublist in self.services for container in sublist.rollback_containers()]

    def can_be_upped(self) -> bool:
        return not any(self.rollback_containers())

    @staticmethod
    def can_be_downed() -> bool:
        return True

    def can_be_removed(self) -> bool:
        return not any(self.rollback_containers()) and any(self.stopped_containers())

    def can_be_restarted(self) -> bool:
        return not any(self.rollback_containers()) and (
            any(self.stopped_containers()) or any(self.running_containers())
        )

    def up(self):
        for service in self.services:
            docker.pull_image(project_name=self.project_name, service_name=service)
        docker.execute_compose_command(self.project_name, ["up", "--detach"])

    def down(self):
        docker.execute_compose_command(self.project_name, ["down"])

    def rm(self):
        docker.execute_compose_command(self.project_name, ["rm", "--force"])

    def restart(self):
        docker.execute_compose_command(self.project_name, ["restart"])


def remove_custom_registry_from_image_name(name: str) -> str:
    return name.replace(settings.STRIP_CUSTOM_REGISTRY, "")
