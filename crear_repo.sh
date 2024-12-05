#!/bin/bash

# Variables necesarias
REPO_NAME=$1
REPO_URL="git@github.com:tu_usuario/$REPO_NAME.git"

if [ -z "$REPO_NAME" ]; then
  echo "Por favor, proporciona el nombre del repositorio como argumento."
  exit 1
fi

# Crear el directorio y moverse a él
mkdir $REPO_NAME && cd $REPO_NAME

# Inicializar Git, hacer commit inicial y conectar con el remoto
git init
echo "# $REPO_NAME" > README.md
git add .
git commit -m "Commit inicial"
git branch -M main
git remote add origin $REPO_URL
git push -u origin main

echo "Repositorio creado y subido exitosamente: $REPO_URL"