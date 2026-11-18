#!/usr/bin/env bash
# Build both images with Cloud Build and deploy them to Cloud Run.
# Run ./deploy/setup.sh once before.
#
# Usage:
#   export PROJECT_ID=my-gcp-project QDRANT_URL=https://xxx.cloud.qdrant.io:6333
#   ./deploy/deploy.sh
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${QDRANT_URL:?set QDRANT_URL}"
REGION="${REGION:-europe-west1}"
BUCKET="${PROJECT_ID}-my-notebook-uploads"
REPO="$REGION-docker.pkg.dev/$PROJECT_ID/my-notebook"
TAG="$(git rev-parse --short HEAD)" # image version = commit
cd "$(dirname "$0")/.."

echo "1. Backend: build + deploy"
# - public URL, but every route except /health needs the API key
# - the GCS bucket is mounted as a folder (needs gen2); uid 1000 = the "app" user of the image
# - 2 CPU / 2 GiB: PDF parsing + local models; timeout 900 s: /ingest can take minutes
# - 0 to 2 instances: free when idle, and a cap on the bill
gcloud builds submit backend --tag "$REPO/backend:$TAG"
gcloud run deploy my-notebook-backend \
  --image "$REPO/backend:$TAG" --region "$REGION" \
  --service-account "my-notebook-backend@$PROJECT_ID.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest,QDRANT_API_KEY=qdrant-api-key:latest,APP_API_KEY=app-api-key:latest \
  --set-env-vars QDRANT_URL="$QDRANT_URL",LOCAL_UPLOAD_DIR=/mnt/uploads \
  --execution-environment gen2 \
  --add-volume name=uploads,type=cloud-storage,bucket="$BUCKET",mount-options="uid=1000;gid=1000" \
  --add-volume-mount volume=uploads,mount-path=/mnt/uploads \
  --cpu 2 --memory 2Gi --timeout 900 \
  --min-instances 0 --max-instances 2

BACKEND_URL="$(gcloud run services describe my-notebook-backend --region "$REGION" --format 'value(status.url)')"

echo "2. Frontend: build + deploy"
gcloud builds submit frontend --tag "$REPO/frontend:$TAG"
gcloud run deploy my-notebook-frontend \
  --image "$REPO/frontend:$TAG" --region "$REGION" \
  --service-account "my-notebook-frontend@$PROJECT_ID.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL="$BACKEND_URL" \
  --set-secrets APP_API_KEY=app-api-key:latest \
  --timeout 900 \
  --cpu 1 --memory 512Mi --min-instances 0 --max-instances 2

FRONTEND_URL="$(gcloud run services describe my-notebook-frontend --region "$REGION" --format 'value(status.url)')"
echo "Backend:  $BACKEND_URL/health"
echo "Frontend: $FRONTEND_URL"
