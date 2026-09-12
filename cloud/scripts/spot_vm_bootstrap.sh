#!/usr/bin/env bash
# ==============================================================================
# One-shot bootstrap for a fresh Ubuntu spot VM (vast.ai / RunPod / Lambda).
# Tested target: Ubuntu 22.04/24.04 + Docker. GPU optional (auto-used if found).
# Usage:  bash cloud/scripts/spot_vm_bootstrap.sh [small|base]
# ==============================================================================
set -euo pipefail
MODEL_SIZE="${1:-small}"
REPO="https://github.com/aswinkumaar06-a11y/SIH_MODEL.git"

echo "==> installing docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || apt-get update && apt-get install -y docker-compose-plugin

echo "==> nvidia container toolkit (best-effort; skipped on CPU VMs)"
if command -v nvidia-smi >/dev/null 2>&1; then
  distribution=$(. /etc/os-release; echo "$ID$VERSION_ID")
  curl -fsSL "https://nvidia.github.io/libnvidia-container/gpgkey" | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg || true
  curl -s -L "https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list" \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list || true
  apt-get update -qq && apt-get install -y -qq nvidia-container-toolkit || true
  nvidia-ctk runtime configure --runtime=docker || true
  systemctl restart docker || true
else
  echo "   (no GPU detected — gateway will run INT8 on CPU, fine for the single-stream demo)"
fi

echo "==> cloning project"
[ -d SIH_MODEL ] || git clone --depth 1 "$REPO"
cd SIH_MODEL/cloud

echo "==> launching stack (gateway ASR_MODEL_SIZE=$MODEL_SIZE + mqtt)"
AGNI_API_TOKEN="${AGNI_API_TOKEN:-$(head -c 24 /dev/urandom | base64)}"
export AGNI_API_TOKEN AGNI_MODEL_SIZE="$MODEL_SIZE"
echo "AGNI_API_TOKEN=$AGNI_API_TOKEN" > .env
docker compose up -d --build

echo "=============================================================="
echo " AGNI-ASR up. Health:"
echo "   curl http://localhost:8000/healthz"
echo " Swagger: http://<vm-ip>:8000/docs    MQTT port: 1883"
echo " API token (keep secret): $AGNI_API_TOKEN"
echo "=============================================================="
