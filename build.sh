#!/bin/bash

echo "============================================"
echo " KREYE LOCALE FILES AN LIY"
echo "============================================"

cd "$(dirname "$0")"

# Verifye si token disponib
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN pa defini nan environment variables"
    echo "Sote pouse GitHub..."
    exit 1
fi

# Git config
git config user.email "render@example.com"
git config user.name "Render Bot"

# Configure remote
git remote set-url origin https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git

# Verifye branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Branch aktyèl: $BRANCH"

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
git add locale/ staticfiles/
if git diff --cached --quiet; then
    echo "✅ Pa gen chanjman pou pouse"
else
    git commit -m "Auto-generate locale files [skip ci]"
    git push origin $BRANCH
    echo "✅ Pouse sou GitHub reyisi"
fi

echo "✅ FINI!"