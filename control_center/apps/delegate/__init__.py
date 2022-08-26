from django.apps import AppConfig


class DelegateConfig(AppConfig):
    name = "control_center.apps.delegate"

    def ready(self):
        from django.contrib.auth.models import Permission

        Permission.__str__ = lambda this: "%s | %s | %s" % (this.content_type.app_label, this.content_type, this.name)


default_app_config = "control_center.apps.delegate.DelegateConfig"
