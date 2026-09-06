#!/bin/bash

echo "============================================"
echo " KREYE LOCALE FILES AN LIY"
echo "============================================"

cd "$(dirname "$0")"

# ENSTALE DJANGO AK GUNICORN DIRÈKTEMAN
echo "[0/6] Enstale Django ak Gunicorn..."
pip install Django gunicorn

# Verifye enstalasyon
python -c "import django; print(f'Django {django.__version__} enstale')"

# Git config
if [ ! -z "$GITHUB_TOKEN" ]; then
    git config user.email "render@example.com"
    git config user.name "Render Bot"
    git remote set-url origin https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git
fi

# Kreye locale
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules

# Korije Plural-Forms
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
fi

# Konpile
python manage.py compilemessages --ignore=.venv --ignore=node_modules

# Kolekte statik
python manage.py collectstatic --noinput

# Pouse sou GitHub
if [ ! -z "$GITHUB_TOKEN" ]; then
    git add locale/ staticfiles/
    if git diff --cached --quiet; then
        echo "✅ Pa gen chanjman"
    else
        git commit -m "Auto-generate locale files [skip ci]"
        git push origin main
    fi
fi

echo "✅ FINI!"