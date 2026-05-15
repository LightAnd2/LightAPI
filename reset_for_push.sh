#!/bin/bash
# Run this once before pushing to remove your personal monitoring data.
# Anyone who clones the repo starts fresh and gets demo endpoints on first run.

echo "Removing local database..."
rm -f backend/lightai.db

echo "Removing trained models..."
rm -rf backend/models/

echo "Done. Safe to push."
