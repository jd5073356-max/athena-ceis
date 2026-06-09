#!/usr/bin/env bash
# Despliegue de Athena en Google Cloud Run — todo en uno.
# Uso:   bash ~/proyectos/athena/deploy_cloudrun.sh
# Te pedirá 2 contraseñas (BD Oracle y wallet). Nada de eso se guarda en disco.
set -euo pipefail
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

PROJ=gen-lang-client-0454730768
REGION=southamerica-west1

echo "==> Proyecto: $PROJ   Región: $REGION"
gcloud config set project "$PROJ" >/dev/null

echo "==> 1/5  Habilitando APIs (puede tardar ~1 min)…"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

echo "==> 2/5  Armando el bundle de secretos (wallet + OCI)…"
rm -rf /tmp/athena-bundle /tmp/athena-bundle.tgz
mkdir -p /tmp/athena-bundle/wallet /tmp/athena-bundle/oci
cp /home/juan/oracle/athena-wallet/* /tmp/athena-bundle/wallet/
cp /home/juan/.oci/oci_api_key.pem  /tmp/athena-bundle/oci/
sed 's#^key_file=.*#key_file=/secrets/oci/oci_api_key.pem#' /home/juan/.oci/config \
  > /tmp/athena-bundle/oci/config
tar czf /tmp/athena-bundle.tgz -C /tmp/athena-bundle .
SZ=$(stat -c%s /tmp/athena-bundle.tgz)
echo "    bundle: $SZ bytes"
[ "$SZ" -gt 1000 ] || { echo "ERROR: el bundle quedó vacío"; exit 1; }

# Crea el secreto si no existe; si existe, agrega una versión nueva.
put_secret() {  # $1=nombre  $2=archivo
  if gcloud secrets describe "$1" >/dev/null 2>&1; then
    gcloud secrets versions add "$1" --data-file="$2" >/dev/null
  else
    gcloud secrets create "$1" --data-file="$2" >/dev/null
  fi
  echo "    secreto: $1 ✔"
}

echo "==> 3/5  Subiendo secretos a Secret Manager…"
umask 077
put_secret athena-bundle /tmp/athena-bundle.tgz

python3 -c "import secrets;print(secrets.token_urlsafe(64))" | tr -d '\n' > /tmp/_sk
put_secret athena-secret-key /tmp/_sk
rm -f /tmp/_sk

# Contraseñas: se leen de tu .env (no se imprimen). Si no están, te las pide.
ENVFILE="$HOME/proyectos/athena/.env"
ORA_PW=$(grep -E '^ORACLE_PASSWORD=' "$ENVFILE" 2>/dev/null | head -1 | cut -d= -f2- || true)
WAL_PW=$(grep -E '^ORACLE_WALLET_PASSWORD=' "$ENVFILE" 2>/dev/null | head -1 | cut -d= -f2- || true)
[ -n "$ORA_PW" ] || { read -rsp '    >> Password de la BD Oracle: ' ORA_PW </dev/tty; echo; }
[ -n "$WAL_PW" ] || { read -rsp '    >> Password del wallet: '     WAL_PW </dev/tty; echo; }
printf '%s' "$ORA_PW" > /tmp/_p1; put_secret athena-oracle-password /tmp/_p1; rm -f /tmp/_p1
printf '%s' "$WAL_PW" > /tmp/_p2; put_secret athena-wallet-password /tmp/_p2; rm -f /tmp/_p2
unset ORA_PW WAL_PW
rm -rf /tmp/athena-bundle /tmp/athena-bundle.tgz

echo "==> 4/5  Dando acceso a los secretos al runtime…"
PROJNUM=$(gcloud projects describe "$PROJ" --format='value(projectNumber)')
SA="$PROJNUM-compute@developer.gserviceaccount.com"
for s in athena-bundle athena-secret-key athena-oracle-password athena-wallet-password; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor" >/dev/null
done
echo "    permisos ✔ ($SA)"

echo "==> 5/5  Build + deploy (esto tarda ~3-5 min)…"
cd "$HOME/proyectos/athena"
gcloud run deploy athena --source . --region "$REGION" --allow-unauthenticated --quiet \
  --memory 512Mi --timeout 120 \
  --set-env-vars "DJANGO_DEBUG=False,DJANGO_ALLOWED_HOSTS=.run.app,DJANGO_CSRF_TRUSTED_ORIGINS=https://*.run.app,DB_ENGINE=oracle,ORACLE_DSN=athena_high,ORACLE_USER=ADMIN,TNS_ADMIN=/secrets/wallet,STORAGE_BACKEND=oci,OCI_NAMESPACE=axsqkomilnv5,OCI_BUCKET=athena-archivos,OCI_REGION=sa-bogota-1,OCI_AUTH=config,OCI_CONFIG_FILE=/secrets/oci/config,OCI_CONFIG_PROFILE=DEFAULT,OCI_PUBLIC=true" \
  --set-secrets "DJANGO_SECRET_KEY=athena-secret-key:latest,ORACLE_PASSWORD=athena-oracle-password:latest,ORACLE_WALLET_PASSWORD=athena-wallet-password:latest,/var/secrets/bundle.tgz=athena-bundle:latest"

echo
echo "============================================================"
echo "  LISTO. Athena está en la web:"
gcloud run services describe athena --region "$REGION" --format='value(status.url)'
echo "  Panel del Rector:  <esa URL>/admin/"
echo "============================================================"
