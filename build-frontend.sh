#!/bin/bash
# Build script for frontend deployment on Render

# Replace placeholder with actual backend URL from environment variable
if [ -n "$BACKEND_URL" ]; then
  sed -i "s|__BACKEND_URL__|$BACKEND_URL|g" frontend/static/config.js
  echo "✅ Backend URL configured: $BACKEND_URL"
else
  echo "⚠️  Warning: BACKEND_URL not set, using empty string"
  sed -i "s|__BACKEND_URL__||g" frontend/static/config.js
fi

echo "✅ Frontend build complete"
