from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import Imagen


@method_decorator(staff_member_required, name="dispatch")
class GaleriaWorkspaceView(View):
    template_name = "admin/galeria_workspace.html"

    def get(self, request):
        imagenes = Imagen.objects.all().order_by("-fecha")
        return render(request, self.template_name, {"imagenes": imagenes})
