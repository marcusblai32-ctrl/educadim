#!/bin/bash

echo "============================================"
echo " RESET LOCALE FILES"
echo "============================================"

cd "$(dirname "$0")"

# 1. Verifye locale efase
echo "[1/5] Verifye locale efase..."
if [ -d "locale/" ]; then
    echo "⚠️ locale/ egziste toujou - efase li..."
    rm -rf locale/
    git add -A locale/
    git commit -m "Efase ansyen locale" 2>/dev/null
    git push origin main
else
    echo "✅ locale/ deja efase"
fi

# 2. Rekòmanse makemessages
echo "[2/5] Rekòmanse makemessages..."
python manage.py makemessages -l ht -l fr

# 3. Korije Plural-Forms ak sed
echo "[3/5] Korije Plural-Forms..."

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
echo "[4/5] Konpile..."
python manage.py compilemessages

# 5. Pouse
echo "[5/5] Pouse..."
git add locale/
git commit -m "Rekreye tradiksyon ak korije Plural-Forms"
git push origin main

echo "✅ FINI!"