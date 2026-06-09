# Desplegar Athena en Google Cloud Run

Athena va como **un solo servicio** (web pública `/` + Panel del Rector `/admin/`)
contra la Oracle ADB y el bucket OCI que ya tienes. Cloud Run entra en el **free
tier** (2M peticiones/mes) → para un colegio, gratis.

Los secretos (contraseña de la BD, wallet, llave OCI) **los cargas tú**: nunca se
guardan en el repo ni en la imagen; viven en Secret Manager y se montan en runtime.

> Ejecuta los bloques en orden desde la carpeta del proyecto.

```bash
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
PROJ=gen-lang-client-0454730768
REGION=southamerica-west1
gcloud config set project "$PROJ"
```

## 1. Habilitar APIs
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com
```

## 2. Crear el bundle de secretos (wallet Oracle + config/llave OCI)
```bash
rm -rf /tmp/athena-bundle /tmp/athena-bundle.tgz
mkdir -p /tmp/athena-bundle/wallet /tmp/athena-bundle/oci
cp /home/juan/oracle/athena-wallet/* /tmp/athena-bundle/wallet/
cp /home/juan/.oci/oci_api_key.pem  /tmp/athena-bundle/oci/
sed 's#^key_file=.*#key_file=/secrets/oci/oci_api_key.pem#' /home/juan/.oci/config \
  > /tmp/athena-bundle/oci/config
tar czf /tmp/athena-bundle.tgz -C /tmp/athena-bundle .
```

## 3. Subir los secretos a Secret Manager
```bash
gcloud secrets create athena-bundle --data-file=/tmp/athena-bundle.tgz

# SECRET_KEY nueva para producción
python3 -c "import secrets;print(secrets.token_urlsafe(64))" | tr -d '\n' \
  | gcloud secrets create athena-secret-key --data-file=-

# Contraseñas (te las pide sin mostrarlas ni dejarlas en el historial)
read -rsp 'Password Oracle ADB: ' P; printf '%s' "$P" \
  | gcloud secrets create athena-oracle-password --data-file=-; unset P; echo
read -rsp 'Password del wallet:  ' P; printf '%s' "$P" \
  | gcloud secrets create athena-wallet-password --data-file=-; unset P; echo

# Limpiar el bundle local
rm -rf /tmp/athena-bundle /tmp/athena-bundle.tgz
```

## 4. Dar acceso a los secretos al runtime de Cloud Run
```bash
PROJNUM=$(gcloud projects describe "$PROJ" --format='value(projectNumber)')
SA="$PROJNUM-compute@developer.gserviceaccount.com"
for s in athena-bundle athena-secret-key athena-oracle-password athena-wallet-password; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
done
```

## 5. Desplegar (build + deploy desde el repo)
```bash
gcloud run deploy athena --source . --region "$REGION" --allow-unauthenticated \
  --memory 512Mi --timeout 120 \
  --set-env-vars "DJANGO_DEBUG=False,DJANGO_ALLOWED_HOSTS=.run.app,DJANGO_CSRF_TRUSTED_ORIGINS=https://*.run.app,DB_ENGINE=oracle,ORACLE_DSN=athena_high,ORACLE_USER=ADMIN,TNS_ADMIN=/secrets/wallet,STORAGE_BACKEND=oci,OCI_NAMESPACE=axsqkomilnv5,OCI_BUCKET=athena-archivos,OCI_REGION=sa-bogota-1,OCI_AUTH=config,OCI_CONFIG_FILE=/secrets/oci/config,OCI_CONFIG_PROFILE=DEFAULT,OCI_PUBLIC=true" \
  --set-secrets "DJANGO_SECRET_KEY=athena-secret-key:latest,ORACLE_PASSWORD=athena-oracle-password:latest,ORACLE_WALLET_PASSWORD=athena-wallet-password:latest,/var/secrets/bundle.tgz=athena-bundle:latest"
```

Al terminar imprime la URL pública. Para obtenerla de nuevo:
```bash
gcloud run services describe athena --region "$REGION" --format='value(status.url)'
```

## 6. Acceso al Panel del Rector
La BD ya tiene el superusuario `rector`. Si no recuerdas la contraseña, reséteala
(actualiza la misma ADB que usa producción):
```bash
cd ~/proyectos/athena && source .venv/bin/activate
python manage.py changepassword rector
```
Entra en `https://<tu-url>.run.app/admin/`.

## Notas
- **Cero downtime de datos:** producción usa la MISMA Oracle ADB que tu entorno local.
- Si una página de la BD da error 500, revisa logs:
  `gcloud run services logs read athena --region "$REGION" --limit 50`
- Si hay OOM (memoria), sube a `--memory 1Gi` y redeploy.
- Para un dominio propio: `gcloud run domain-mappings create --service athena --domain panel.tucolegio.edu.co --region "$REGION"`.
