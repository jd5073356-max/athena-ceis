from django.urls import path

from . import views

app_name = "panel_rector"

urlpatterns = [
    path("galeria/", views.GaleriaWorkspaceView.as_view(), name="galeria_workspace"),
]
