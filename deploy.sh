#!/bin/bash
set -e

echo "================================================================="
echo " Stadium Crowd & Emergency Orchestrator — GCloud Deployment      "
echo "================================================================="

# Load variables from local .env if it exists
if [ -f .env ]; then
    echo "Loading configuration from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Resolve project and region
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
IMAGE_NAME="stadium-orchestrator"
REPO="stadium-repo"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:latest"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ ERROR: Google Cloud Project ID is not configured."
    echo "Set GOOGLE_CLOUD_PROJECT in .env or run: gcloud config set project [PROJECT_ID]"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY is not set in .env file."
    echo "Get a key from: https://aistudio.google.com/app/api-keys"
    exit 1
fi

echo "Deploying with:"
echo "  👉 GCP Project : $PROJECT_ID"
echo "  👉 Region      : $REGION"
echo "  👉 Image       : $IMAGE_TAG"
echo "-----------------------------------------------------------------"

# Enable required GCP APIs
echo "⚙️  Enabling required Google Cloud APIs..."
gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com \
    generativelanguage.googleapis.com \
    --project "$PROJECT_ID"

# Create Artifact Registry repository if it doesn't exist
echo "📦 Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe "$REPO" \
    --location="$REGION" --project="$PROJECT_ID" &>/dev/null || \
gcloud artifacts repositories create "$REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --description="Stadium Orchestrator Docker images"

# Build image via Cloud Build and push to Artifact Registry
echo "🏗️  Building Docker image with Cloud Build..."
gcloud builds submit \
    --tag "$IMAGE_TAG" \
    --project "$PROJECT_ID"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$IMAGE_NAME" \
    --image "$IMAGE_TAG" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION},GEMINI_API_KEY=${GEMINI_API_KEY}" \
    --project "$PROJECT_ID"

echo "-----------------------------------------------------------------"
echo "🎉 SUCCESS! Application deployed to Cloud Run."
echo "🌐 Live URL:"
gcloud run services describe "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)'
