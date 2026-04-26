#!/bin/bash
# ---------------------------------------------------------------------------
# Empaqueta el backend de HeimdALL para AWS Lambda usando Docker.
# Requiere Docker instalado y en ejecución.
# Ejecutar desde la carpeta backend/
# ---------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/lambda_build"
ZIP_PATH="$SCRIPT_DIR/../terraform/sandbox/backend_lambda.zip"

echo "→ Limpiando build anterior..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "→ Instalando dependencias para linux/x86_64 con Docker..."
docker run --rm \
  --platform linux/x86_64 \
  --entrypoint pip \
  -v "$SCRIPT_DIR":/var/task \
  public.ecr.aws/lambda/python:3.12 \
  install -r /var/task/requirements.txt -t /var/task/lambda_build/ --quiet

echo "→ Copiando código de la aplicación..."
cp -r "$SCRIPT_DIR/app" "$BUILD_DIR/"

echo "→ Creando ZIP..."
cd "$BUILD_DIR"
zip -r "$ZIP_PATH" . -q
cd -

echo "✓ Lambda package listo: $ZIP_PATH"
echo "  Tamaño: $(du -sh "$ZIP_PATH" | cut -f1)"
