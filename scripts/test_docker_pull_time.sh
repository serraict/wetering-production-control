#!/bin/bash
# Script to test and time Docker image pull operations

# Set the registry and image name
REGISTRY=${REGISTRY:-ghcr.io}
REPO=${REPO:-serraict/wetering-production-control}
TAG=${TAG:-latest}

# Function to time the pull operation
time_pull() {
  echo "===== Testing pull time for $REGISTRY/$REPO:$TAG ====="
  
  # Remove the image first to ensure a clean pull
  # echo "Removing existing image..."
  # docker rmi $REGISTRY/$REPO:$TAG >/dev/null 2>&1 || true
  
  # Time the pull operation
  echo "Pulling image..."
  time docker pull $REGISTRY/$REPO:$TAG
  
  echo "===== Pull completed ====="
  echo ""
}

# Main script
echo "Docker Pull Time Test"
echo "====================="
echo "This script measures the time it takes to pull a Docker image."
echo ""

# Test the pull time
time_pull

echo "To test with a different tag:"
echo "TAG=v0.1.14 $0"
echo ""

echo "To compare before and after optimization:"
echo "1. Run this script with the old image tag"
echo "2. Make your code changes"
echo "3. Build and push a new image"
echo "4. Run this script with the new image tag"
echo "5. Compare the times"
