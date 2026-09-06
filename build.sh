#!/bin/bash

echo "============================================"
echo " RESET LOCALE FILES"
echo "============================================"

cd "$(dirname "$0")"

# 0. Enstale depandans yo si yo pa enstale
echo "[0/6] Verifye depandans..."
if ! python -c "import django" 2>/dev/null; then
    echo "⚠️ Django pa enstale - enstale depandans yo..."
    pip install -r requirements.txt
fi

# 1. Verifye locale efase
echo "[1/6] Verifye locale efase..."
if [ -d "locale/" ]; then
    echo "⚠️ locale/ egziste toujou - efase li..."
    rm -rf locale/
fi

# 2. Rekòmanse makemessages
echo "[2/6] Rekòmanse makemessages..."
python manage.py makemessages -l ht -l fr

# 3. Korije Plural-Forms ak sed
echo "[3/6] Korije Plural-Forms..."

# Pou Kreyòl Ayisyen (ht)
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
    echo "✅ ht korije"
else
    echo "⚠️ ht: fichye pa egziste"
fi

# Pou Franse (fr)
if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
    echo "✅ fr korije"
else
    echo "⚠️ fr: fichye pa egziste"
fi

# 4. Konpile
echo "[4/6] Konpile..."
python manage.py compilemessages

# 5. Config ak pouse
echo "[5/6] Config git ak pouse..."
# Config git si pa deja fèt
git config user.email "votre-email@example.com" 2>/dev/null
git config user.name "Votre Nom" 2>/dev/null

# Verifye si origin remote egziste
if ! git remote | grep -q "origin"; then
    echo "⚠️ Pa gen origin remote - ajoute li..."
    echo "Ranplase URL sa ak URL repo ou:"
    echo "git remote add origin https://github.com/USERNAME/REPO.git"
    exit 1
fi

git add locale/
git commit -m "Rekreye tradiksyon ak korije Plural-Forms"
git push origin main

# 6. Enstale gunicorn si sa nesesè
echo "[6/6] Verifye gunicorn..."
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️ Gunicorn pa enstale - enstale li..."
    pip install gunicorn
fi

echo "✅ FINI!"