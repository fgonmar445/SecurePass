from django.urls import path

from passwords import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("add/", views.AddPasswordView.as_view(), name="add_password"),
    path("generate/", views.generate_password, name="generate_password"),
    path("<uuid:pk>/delete/", views.DeletePasswordView.as_view(), name="delete_password"),
    path("<uuid:pk>/reveal/", views.reveal_password, name="reveal_password"),
]
