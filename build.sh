#!/bin/bash

echo "============================================"
echo " BUILD - EDUCAdIM"
echo "============================================"

cd "$(dirname "$0")"

# Enstale depandans
echo "[1/6] Enstale depandans..."
pip install -r requirements.txt

# Kreye dosye locale si li pa egziste
echo "[2/6] Kreye dosye locale..."
mkdir -p locale

# Kreye messages
echo "[3/6] Kreye nouvo messages..."
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules 2>/dev/null || echo "Makemessages pa enpotan si pa gen chanjman"

# Korije Plural-Forms
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
fi

# Konpile messages
echo "[4/6] Konpile messages..."
python manage.py compilemessages --ignore=.venv --ignore=node_modules 2>/dev/null || echo "Compilemessages pa enpotan"

# Kolekte statik
echo "[5/6] Kolekte fichye statik..."
python manage.py collectstatic --noinput

# Migrasyon database
echo "[6/6] Migrasyon database..."
python manage.py migrate --noinput

echo "============================================"
echo " BUILD FINI AVEC SUKSE!"
echo "============================================"