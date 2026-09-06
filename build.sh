#!/bin/bash

echo "============================================"
echo " BUILD SIMPLE - SAN PUSH"
echo "============================================"

cd "$(dirname "$0")"

# Enstale depandans
echo "[1/5] Enstale depandans..."
pip install -r requirements.txt

# Kreye locale
echo "[2/5] Kreye nouvo locale..."
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules

# Korije Plural-Forms
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
fi

# Konpile
echo "[3/5] Konpile messages..."
python manage.py compilemessages --ignore=.venv --ignore=node_modules

# Kolekte statik
echo "[4/5] Kolekte fichye statik..."
python manage.py collectstatic --noinput

echo "[5/5] FINI! Pa bezwen pouse sou GitHub."