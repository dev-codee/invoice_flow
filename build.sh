#!/usr/bin/env bash
# Render build script — exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Attempt migrations. If the DB is not reachable during build (internal hostname),
# this will fail gracefully and migrations must run via preDeployCommand or manually.
python manage.py migrate --no-input || echo "⚠️  Migration skipped (DB not reachable during build). Will run at deploy time."
