from typing import Dict, Optional

from django.conf import settings
from importlib.metadata import version, PackageNotFoundError


def app_version() -> Optional[str]:
    try:
        return version("docker_compose_control_center")
    except PackageNotFoundError:
        # package is not installed
        pass


base_context = {
    "title": settings.SITE_TITLE,
    "auto_refresh": settings.AUTO_REFRESH,
    "disable_container_actions": settings.DISABLE_SERVICE_CONTAINER_ACTIONS,
    "app_version": app_version(),
}


def context(items=None) -> Dict:
    if items is None:
        items = {}
    return {**base_context, **items}
