from subprocess import CalledProcessError
from threading import Lock

from django.shortcuts import render
from docker.errors import NotFound

from control_center.apps.compose_ui.views import context

global_system_lock = Lock()


# checks for CalledProcessError and ThreadError and redirects appropriately
# if lock is True, lock the function into the global system lock (only one command at a time)
def view_check_errors_redirect(error_message: str, lock: bool = False):
    def decorator(view):
        def wrapper(request, *args, **kwargs):
            try:
                if lock:
                    if global_system_lock.locked():
                        return render(request, "compose_ui/errors/system_busy.html", context())
                    with global_system_lock:
                        return view(request, *args, **kwargs)
                else:
                    return view(request, *args, **kwargs)
            except NotFound as error:
                return render(
                    request, "compose_ui/errors/system_error.html", context({"error_message": error.explanation})
                )
            except CalledProcessError:
                return render(request, "compose_ui/errors/system_error.html", context({"error_message": error_message}))

        return wrapper

    return decorator
