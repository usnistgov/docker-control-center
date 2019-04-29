# checks permission from function argument (app_label_arg_name)
# i.e. checks user.has_perm(${app_label}.perm_code)
from django.contrib.auth.models import User


def view_has_perm_from_arg(app_label_arg_name: str, perm_code: str, unauthorized_function):
    def decorator(view):
        def wrapper(request, *args, **kwargs):
            app_label_arg = kwargs.get(app_label_arg_name)
            user: User = request.user
            if user.has_perm(app_label_arg + "." + perm_code):
                return view(request, *args, **kwargs)
            else:
                unauthorized_function()

        return wrapper

    return decorator
