#!/bin/bash

echo "============================================"
echo " KREYE LOCALE FILES AN LIY"
echo "============================================"

cd "$(dirname "$0")"

# 0. Verifye git config
echo "[0/7] Verifye git config..."
git config user.email "render@example.com"
git config user.name "Render Bot"

# Configure remote ak token
git remote set-url origin https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git

# 1. Efase ansyen locale
echo "[1/7] Efase ansyen locale..."
if [ -d "locale/" ]; then
    rm -rf locale/
fi

# 2. Kreye nouvo locale
echo "[2/7] Kreye nouvo locale..."
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules

# 3. Korije Plural-Forms
echo "[3/7] Korije Plural-Forms..."
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
    echo "✅ ht korije"
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
    echo "✅ fr korije"
fi

# 4. Konpile messages
echo "[4/7] Konpile messages..."
python manage.py compilemessages --ignore=.venv --ignore=node_modules

# 5. Kolekte statik
echo "[5/7] Kolekte fichye statik..."
python manage.py collectstatic --noinput

# 6. Pouse sou GitHub
echo "[6/7] Pouse sou GitHub..."
git add locale/
git add staticfiles/

# Tcheke si gen chanjman
if git diff --cached --quiet; then
    echo "✅ Pa gen nouvo chanjman"
else
    git commit -m "Kreye tradiksyon ak kolekte statik [CI]"
    git push origin main
    echo "✅ Pouse sou GitHub konplè"
fi

# 7. Verifye siksè
echo "[7/7] Verifye deplwaman..."
echo "✅ FINI!"

# Kontinye ak deplwaman nòmal
echo "=== KONTINYE AK DEPLWAMAN ==="