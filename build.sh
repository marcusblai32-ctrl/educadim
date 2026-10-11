#!/bin/bash

set -o errexit

echo "============================================"
echo " BUILD - EDUCADIM"
echo "============================================"

cd "$(dirname "$0")"

echo "[1/6] Enstale depandans Python..."
pip install -r requirements.txt

echo "[2/6] Prepare dosye locale..."
mkdir -p locale

echo "[3/6] Kreye/mete ajou messages..."

python manage.py makemessages -l ht -l fr \
  --ignore=.venv \
  --ignore=node_modules

echo "[4/6] Konpile messages..."

python manage.py compilemessages \
  --ignore=.venv \
  --ignore=node_modules

echo "[5/6] Kolekte fichye statik..."

python manage.py collectstatic --noinput

echo "[6/6] Aplike migrasyon database..."

python manage.py migrate --noinput --run-syncdb

echo "============================================"
echo " BUILD FINI AVEC SUKSE!"
echo "============================================"