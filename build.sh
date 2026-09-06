#!/bin/bash

echo "============================================"
echo " KREYE LOCALE FILES AN LIY"
echo "============================================"

cd "$(dirname "$0")"

# ENSTALE DEPANDANS YO
echo "[0/7] Enstale depandans..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt pa egziste!"
    echo "Enstale depandans debaz..."
    pip install Django gunicorn django-environ
fi

# Verifye Django enstale
echo "Verifye Django..."
python -c "import django; print(f'Django {django.__version__} ✓')" || exit 1

# Verifye django-environ
echo "Verifye django-environ..."
python -c "import environ; print('django-environ ✓')" || {
    echo "Enstale django-environ..."
    pip install django-environ
}

# Git config si token disponib
if [ ! -z "$GITHUB_TOKEN" ]; then
    echo "Configure git..."
    git config user.email "render@example.com"
    git config user.name "Render Bot"
    git remote set-url origin https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git
fi

# Kreye locale
echo "[1/7] Kreye nouvo locale..."
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules

# Korije Plural-Forms
echo "[2/7] Korije Plural-Forms..."
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
    echo "✅ ht korije"
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
    echo "✅ fr korije"
fi

# Konpile messages
echo "[3/7] Konpile messages..."
python manage.py compilemessages --ignore=.venv --ignore=node_modules

# Kolekte statik (si django.contrib.staticfiles nan INSTALLED_APPS)
echo "[4/7] Kolekte fichye statik..."
python manage.py collectstatic --noinput 2>/dev/null || {
    echo "⚠️ collectstatic pa disponib - sote"
}

# Pouse sou GitHub
echo "[5/7] Pouse sou GitHub..."
if [ ! -z "$GITHUB_TOKEN" ]; then
    git add locale/ staticfiles/ 2>/dev/null
    if git diff --cached --quiet; then
        echo "✅ Pa gen chanjman"
    else
        git commit -m "Auto-generate locale files [skip ci]"
        git push origin main
        echo "✅ Pouse sou GitHub reyisi"
    fi
fi

echo "[6/7] FINI!"