from pydoc import locate

from django.conf import settings
from django.contrib.auth import logout, authenticate, login, REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.urls import reverse, resolve
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_GET

from control_center.libs.authentication.backends import (
    RemoteUserAuthenticationBackend,
    NginxKerberosAuthorizationHeaderAuthenticationBackend,
)


@require_http_methods(["GET", "POST"])
@sensitive_post_parameters("password")
def login_user(request):
    backends = [locate(backend) for backend in settings.AUTHENTICATION_BACKENDS]
    if RemoteUserAuthenticationBackend in backends or NginxKerberosAuthorizationHeaderAuthenticationBackend in backends:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "authentication/authorization_failed.html")

    dictionary = {"title": settings.LOGIN_TITLE, "user_name_or_password_incorrect": False}
    if request.method == "GET":
        return render(request, "authentication/login.html", dictionary)
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        try:
            next_page = request.GET[REDIRECT_FIELD_NAME]
            resolve(next_page)  # Make sure the next page is a legitimate URL for the system
        except:
            next_page = reverse("index")
        return HttpResponseRedirect(next_page)
    dictionary["user_name_or_password_incorrect"] = True
    return render(request, "authentication/login.html", dictionary)


@require_GET
def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))
