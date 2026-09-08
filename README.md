
EducDim — modernized Django handoff
This archive contains the EducDim Django LMS source and the latest UI modernization work. It is prepared for copying into a GitHub repository without the Replit runtime scaffold.
Included
Existing Django apps and business logic
Responsive shared navigation and course search
Refreshed public home page styling
Connected todo workspace with filtering, create/edit/delete, and status toggles
Native Haitian Creole translation files
Replit workflow configuration and deployment files
Intentionally excluded
Git history and credentials
Local SQLite database
Python environments and caches
Node modules and unrelated artifact scaffold files
User-uploaded media
Local setup
python3.11 -m pip install -r requirements.txt
cp .env.dist .env
python3.11 manage.py migrate --run-syncdb
python3.11 manage.py collectstatic --noinput
python3.11 manage.py runserver 0.0.0.0:8000
Set DATABASE_URL to the intended database before any migration outside local development. Configure SECRET_KEY, BREVO_*, and TELERIVET_* through your deployment secret manager; do not commit them.
Replit preview
The included .replit workflow intentionally clears DATABASE_URL for local UI preview so the imported app uses SQLite instead of inheriting an unrelated workspace PostgreSQL URL. Change that only when the target database schema is confirmed.