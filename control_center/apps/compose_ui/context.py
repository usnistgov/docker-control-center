from typing import Dict

from django.conf import settings
from pkg_resources import get_distribution, DistributionNotFound


def app_version() -> str:
    try:
        return get_distribution("docker_compose_control_center").version
    except DistributionNotFound:
        # package is not installed
        pass


base_context = {
    "title": settings.SITE_TITLE,
    "auto_refresh": settings.AUTO_REFRESH,
    "disable_container_actions": settings.DISABLE_SERVICE_CONTAINER_ACTIONS,
    "app_version": app_version(),
}


def context(items: Dict = {}) -> Dict:
    return {**base_context, **items}
