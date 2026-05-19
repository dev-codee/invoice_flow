#!/usr/bin/env bash
# Render build script — exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Migrate only if DATABASE_URL uses an external hostname.
# Render internal hostnames (ending in -a) are NOT resolvable during builds,
# so we skip migrations here and run them in the start/release command instead.
# This prevents "could not translate host name" build failures.
echo "Skipping migrations during build — they will run at release/start time."
