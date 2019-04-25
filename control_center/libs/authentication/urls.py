from django.urls import path

from . import views

urlpatterns = [
    # login url
    path("login", views.login_user, name="login"),
    # logout url
    path("logout", views.logout_user, name="logout"),
]
