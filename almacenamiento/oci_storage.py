"""
Integración con Oracle Cloud Object Storage.

Este es un backend de almacenamiento de Django: cuando STORAGE_BACKEND=oci,
los FileField (guías PDF, imágenes) suben el archivo a un bucket de Object
Storage y en la base de datos se guarda SOLO la ruta (object name). Así Oracle
Database se mantiene liviano.

En desarrollo NO se usa este archivo: el almacenamiento por defecto es local
(media/). El SDK `oci` solo se importa cuando este backend se usa de verdad,
por eso instalarlo es opcional para correr en local.

Variables de entorno necesarias (producción):
    STORAGE_BACKEND=oci
    OCI_NAMESPACE        espacio de nombres del tenancy
    OCI_BUCKET           nombre del bucket
    OCI_REGION           ej. sa-bogota-1
    OCI_AUTH             "config" (por defecto) | "instance_principal"
    OCI_CONFIG_FILE      ruta al archivo de config OCI (def. ~/.oci/config)
    OCI_CONFIG_PROFILE   perfil dentro del config (def. DEFAULT)
    OCI_PUBLIC           "true" si el bucket es público (URL directa) | "false"
    OCI_PAR_BASE_URL     (opcional) URL base de un Pre-Authenticated Request
                         si el bucket es privado y se sirve por PAR.
"""
import os
from urllib.parse import quote

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


def _env(clave, defecto=None):
    return os.environ.get(clave, defecto)


@deconstructible
class AlmacenamientoObjectStorage(Storage):
    """Backend de Django sobre Oracle Cloud Object Storage."""

    def __init__(self):
        self.namespace = _env("OCI_NAMESPACE")
        self.bucket = _env("OCI_BUCKET")
        self.region = _env("OCI_REGION")
        self.publico = str(_env("OCI_PUBLIC", "false")).lower() in ("1", "true", "yes", "si")
        self.par_base = _env("OCI_PAR_BASE_URL")  # opcional
        self._cliente = None

    # --- Cliente OCI (perezoso) --------------------------------------------
    @property
    def cliente(self):
        """Crea el ObjectStorageClient solo cuando se necesita."""
        if self._cliente is None:
            import oci  # import perezoso: solo en producción con STORAGE_BACKEND=oci

            if str(_env("OCI_AUTH", "config")).lower() == "instance_principal":
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                self._cliente = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
            else:
                config = oci.config.from_file(
                    file_location=_env("OCI_CONFIG_FILE", "~/.oci/config"),
                    profile_name=_env("OCI_CONFIG_PROFILE", "DEFAULT"),
                )
                self._cliente = oci.object_storage.ObjectStorageClient(config)
        return self._cliente

    # --- API de Storage de Django ------------------------------------------
    def _save(self, name, content):
        """Sube el archivo al bucket. Devuelve el object name (la ruta que se
        guarda en la base)."""
        content.seek(0)
        datos = content.read()
        self.cliente.put_object(self.namespace, self.bucket, name, datos)
        return name

    def _open(self, name, mode="rb"):
        respuesta = self.cliente.get_object(self.namespace, self.bucket, name)
        return ContentFile(respuesta.data.content, name=name)

    def exists(self, name):
        """OCI siempre genera un nombre nuevo si hay colisión (ver
        get_available_name), así que reportamos que no existe y dejamos que
        _save escriba con el nombre ya hecho único."""
        return False

    def delete(self, name):
        try:
            self.cliente.delete_object(self.namespace, self.bucket, name)
        except Exception:
            # Si el objeto ya no está, no es un error fatal para Django.
            pass

    def size(self, name):
        cab = self.cliente.head_object(self.namespace, self.bucket, name)
        return int(cab.headers.get("Content-Length", 0))

    def url(self, name):
        ruta = quote(name)
        if self.par_base:
            # Bucket privado servido por Pre-Authenticated Request.
            return f"{self.par_base.rstrip('/')}/{ruta}"
        # URL nativa del objeto (requiere bucket público para acceso directo).
        return (
            f"https://objectstorage.{self.region}.oraclecloud.com"
            f"/n/{self.namespace}/b/{self.bucket}/o/{ruta}"
        )

    def get_available_name(self, name, max_length=None):
        """Evita sobrescrituras añadiendo un sufijo aleatorio corto al nombre."""
        import uuid

        carpeta, archivo = os.path.split(name)
        base, ext = os.path.splitext(archivo)
        unico = f"{base}-{uuid.uuid4().hex[:8]}{ext}"
        return os.path.join(carpeta, unico) if carpeta else unico
