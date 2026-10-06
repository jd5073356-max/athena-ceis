import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Suba los archivos locales de media/ y documentos_prod/ a Cloudflare R2"

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        docs_prod = Path(settings.BASE_DIR) / "documentos_prod"

        endpoint = "https://2437c55c10f2f7c1dd8e879e832cd97c.r2.cloudflarestorage.com"
        access_key = "02fc89c6dbfe4f40f4a928e05aab975e"
        secret_key = "4aff049ec9df94700f993e0d62a42892700ec4bcecf94c023e2d25e2607cd144"
        bucket_name = "athena"

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto"
        )

        files_to_upload = []

        if media_root.exists():
            for root, _, files in os.walk(media_root):
                for f in files:
                    file_path = Path(root) / f
                    rel_path = file_path.relative_to(media_root)
                    files_to_upload.append((file_path, str(rel_path)))

        if docs_prod.exists():
            for root, _, files in os.walk(docs_prod):
                for f in files:
                    file_path = Path(root) / f
                    rel_path = file_path.relative_to(docs_prod)
                    files_to_upload.append((file_path, f"documentos/{rel_path}"))

        self.stdout.write(self.style.SUCCESS(f"Encontrados {len(files_to_upload)} archivos locales para subir a Cloudflare R2..."))

        def upload_single_file(file_info):
            file_path, s3_key = file_info
            ext = file_path.suffix.lower()
            content_type = "binary/octet-stream"
            if ext in (".pdf",):
                content_type = "application/pdf"
            elif ext in (".png",):
                content_type = "image/png"
            elif ext in (".jpg", ".jpeg"):
                content_type = "image/jpeg"
            elif ext in (".webp",):
                content_type = "image/webp"

            try:
                s3.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={"ContentType": content_type}
                )
                return True, s3_key
            except Exception as err:
                return False, f"{s3_key}: {err}"

        uploaded = 0
        failed = 0
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(upload_single_file, item) for item in files_to_upload]
            for future in as_completed(futures):
                success, msg = future.result()
                if success:
                    uploaded += 1
                    if uploaded % 50 == 0 or uploaded == len(files_to_upload):
                        self.stdout.write(self.style.SUCCESS(f"  Progreso: {uploaded}/{len(files_to_upload)} archivos subidos..."))
                else:
                    failed += 1
                    self.stderr.write(self.style.ERROR(f"  Error al subir {msg}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 SUBIDA COMPLETADA! {uploaded} archivos subidos exitosamente a Cloudflare R2 ({failed} fallidos)."))
