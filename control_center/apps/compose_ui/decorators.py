from subprocess import CalledProcessError
from threading import ThreadError, Lock

from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import render

from control_center.apps.compose_ui.views import context

global_system_lock = Lock()


# checks permission from function argument (app_label_arg_name)
# i.e. checks user.has_perm(${app_label}.perm_code)
def view_has_perm_from_arg(app_label_arg_name: str, perm_code: str):
    def decorator(view):
        def wrapper(request, *args, **kwargs):
            app_label_arg = kwargs.get(app_label_arg_name)
            user: User = request.user
            if user.has_perm(app_label_arg + "." + perm_code):
                return view(request, *args, **kwargs)
            else:
                return HttpResponseForbidden  # 403 Forbidden is better than 404

        return wrapper

    return decorator


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
            except CalledProcessError:
                return render(request, "compose_ui/errors/system_error.html", context({"error_message": error_message}))

        return wrapper

    return decorator
