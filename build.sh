#!/bin/bash

echo "============================================"
echo " KREYE LOCALE FILES AN LIY"
echo "============================================"

cd "$(dirname "$0")"

# ENSTALE DEPANDANS YO
echo "[0/8] Enstale depandans..."
pip install -r requirements.txt

# Verifye Django ak django-environ
python -c "import django" 2>/dev/null || exit 1
python -c "import environ" 2>/dev/null || pip install django-environ

# CONFIGURE GIT PROPERLY
echo "[1/8] Configure git..."
git config user.email "render@example.com"
git config user.name "Render Bot"

# Verifye si origin egziste, si non ajoute li
if ! git remote | grep -q "origin"; then
    echo "Ajoute origin remote..."
    if [ ! -z "$GITHUB_USERNAME" ] && [ ! -z "$GITHUB_REPO" ]; then
        if [ ! -z "$GITHUB_TOKEN" ]; then
            git remote add origin https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git
        else
            git remote add origin https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git
        fi
    else
        echo "⚠️ GITHUB_USERNAME oswa GITHUB_REPO pa defini"
    fi
fi

# Verifye branch aktyèl
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Branch: $CURRENT_BRANCH"

# Kreye locale
echo "[2/8] Kreye nouvo locale..."
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules

# Korije Plural-Forms
echo "[3/8] Korije Plural-Forms..."
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
    echo "✅ ht korije"
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
    echo "✅ fr korije"
fi

# Konpile messages
echo "[4/8] Konpile messages..."
python manage.py compilemessages --ignore=.venv --ignore=node_modules

# Kolekte statik
echo "[5/8] Kolekte fichye statik..."
python manage.py collectstatic --noinput 2>/dev/null || echo "⚠️ collectstatic pa disponib"

# Commit chanjman yo
echo "[6/8] Commit chanjman..."
git add locale/ staticfiles/ 2>/dev/null

if git diff --cached --quiet; then
    echo "✅ Pa gen chanjman"
else
    git commit -m "Auto-generate locale files [skip ci]"
fi

# Pouse sou GitHub
echo "[7/8] Pouse sou GitHub..."
if git remote | grep -q "origin"; then
    git push origin $CURRENT_BRANCH 2>/dev/null || {
        echo "⚠️ Push echwe, ap eseye ak HEAD..."
        git push origin HEAD 2>/dev/null || echo "❌ Push echwe - tcheke credentials"
    }
else
    echo "⚠️ Pa gen origin remote - pa ka pouse"
fi

echo "[8/8] FINI!"