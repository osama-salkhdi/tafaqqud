from django.urls import path
from attendance import views

urlpatterns = [
    path("", views.index),
    path("sw.js", views.service_worker),
    path("api/ping", views.ping),
    path("api/state", views.state),
    path("api/push", views.push),
    path("api/login", views.login),
    path("api/me", views.me),
    path("api/reset", views.reset),
]
