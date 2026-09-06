#!/bin/bash

echo "============================================"
echo " RESET LOCALE FILES (BUILD)"
echo "============================================"

cd "$(dirname "$0")"

# Verifye depandans
if ! python -c "import django" 2>/dev/null; then
    pip install -r requirements.txt
fi

# Efase ansyen locale
if [ -d "locale/" ]; then
    rm -rf locale/
fi

# Kreye nouvo locale (sèlman pou pwojè ou)
python manage.py makemessages -l ht -l fr --ignore=.venv --ignore=node_modules --ignore=staticfiles

# Korije Plural-Forms
if [ -f "locale/ht/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n != 1);/' locale/ht/LC_MESSAGES/django.po
    echo "✅ ht korije"
fi

if [ -f "locale/fr/LC_MESSAGES/django.po" ]; then
    sed -i 's/nplurals=INTEGER; plural=EXPRESSION;/nplurals=2; plural=(n > 1);/' locale/fr/LC_MESSAGES/django.po
    echo "✅ fr korije"
fi

# Konpile
python manage.py compilemessages --ignore=.venv --ignore=node_modules --ignore=staticfiles

echo "✅ FINI! Locale pare."