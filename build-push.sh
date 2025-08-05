#!/bin/bash

# Docker registry and image info
REGISTRY="irokr"
IMAGE_NAME="izof"
TAG="${1:-latest}"

# Full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

echo "Building multi-arch Docker image: $FULL_IMAGE_NAME"

docker buildx version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[ERROR] Docker buildx가 설치되어 있지 않습니다. Docker Desktop 최신 버전 또는 buildx 플러그인을 설치하세요."
    exit 1
fi

# 멀티플랫폼 빌드 및 푸시
PLATFORMS="linux/amd64,linux/arm64"
docker buildx build --platform=$PLATFORMS -t "$FULL_IMAGE_NAME" --push .

if [ $? -eq 0 ]; then
    echo "Build & push successful!"
    echo "Image available at: $FULL_IMAGE_NAME (for $PLATFORMS)"
else
    echo "Build or push failed!"
    exit 1
fi