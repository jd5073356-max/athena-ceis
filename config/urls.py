"""
Rutas raíz de Athena.

- /admin/  → Panel del Rector (Django Admin, login obligatorio).
- /        → Web pública (padres y estudiantes).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", include("panel_rector.urls")),
    path("admin/", admin.site.urls),         # Panel del Rector
    path("", include("web_publica.urls")),   # Web pública
]

# En desarrollo, Django sirve los archivos subidos (media/). En producción los
# sirve Object Storage / el servidor web, no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
