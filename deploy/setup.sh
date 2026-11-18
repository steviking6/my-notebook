#!/usr/bin/env bash
# One-time GCP setup for My Notebook. Safe to re-run: existing resources are kept.
#
# Usage:
#   export PROJECT_ID=my-gcp-project QDRANT_URL=https://xxx.cloud.qdrant.io:6333
#   export OPENAI_API_KEY=sk-... QDRANT_API_KEY=...
#   ./deploy/setup.sh
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"
: "${QDRANT_API_KEY:?set QDRANT_API_KEY}"
REGION="${REGION:-europe-west1}"
BUCKET="${PROJECT_ID}-my-notebook-uploads"

gcloud config set project "$PROJECT_ID"

echo "1. Enable the APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com storage.googleapis.com

echo "2. Docker repository (Artifact Registry)"
gcloud artifacts repositories describe my-notebook --location="$REGION" >/dev/null 2>&1 ||
  gcloud artifacts repositories create my-notebook --repository-format=docker --location="$REGION"

echo "3. Bucket for the uploaded files"
gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1 ||
  gcloud storage buckets create "gs://$BUCKET" --location="$REGION" --uniform-bucket-level-access

echo "4. Secrets (Secret Manager): never in the image, never in git"
create_secret() { # name value
  if gcloud secrets describe "$1" >/dev/null 2>&1; then
    echo "   $1 exists (kept)"
  else
    printf '%s' "$2" | gcloud secrets create "$1" --data-file=-
  fi
}
create_secret openai-api-key "$OPENAI_API_KEY"
create_secret qdrant-api-key "$QDRANT_API_KEY"
create_secret app-api-key "$(openssl rand -hex 32)" # shared key frontend -> backend

echo "5. One service account per service, with only the rights it needs"
for sa in my-notebook-backend my-notebook-frontend; do
  gcloud iam service-accounts describe "$sa@$PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "$sa"
done
BACKEND_SA="my-notebook-backend@$PROJECT_ID.iam.gserviceaccount.com"
FRONTEND_SA="my-notebook-frontend@$PROJECT_ID.iam.gserviceaccount.com"

for secret in openai-api-key qdrant-api-key app-api-key; do
  gcloud secrets add-iam-policy-binding "$secret" --quiet \
    --member="serviceAccount:$BACKEND_SA" --role=roles/secretmanager.secretAccessor >/dev/null
done
gcloud secrets add-iam-policy-binding app-api-key --quiet \
  --member="serviceAccount:$FRONTEND_SA" --role=roles/secretmanager.secretAccessor >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --quiet \
  --member="serviceAccount:$BACKEND_SA" --role=roles/storage.objectUser >/dev/null

echo "Done. Next: ./deploy/deploy.sh"
