#!/bin/bash
# Build script for Cloudflare Pages deployment

echo "🚀 Preparing Vehicular System for deployment..."

# Create necessary directories
mkdir -p dist/static/css
mkdir -p dist/static/js
mkdir -p dist/api

# Copy all HTML files
cp *.html dist/ 2>/dev/null || echo "No HTML files to copy"

# Copy CSS files
cp static/css/*.css dist/static/css/ 2>/dev/null || echo "No CSS files to copy"

# Copy JavaScript files
cp static/js/*.js dist/static/js/ 2>/dev/null || echo "No JS files to copy"

# Copy configuration files
cp _headers dist/_headers 2>/dev/null || echo "No _headers file"
cp _redirects dist/_redirects 2>/dev/null || echo "No _redirects file"

# Copy any additional static assets
cp -r static/* dist/static/ 2>/dev/null || echo "No additional static files"

echo "✅ Build completed! Files ready in dist/ directory"
echo "📁 Deployment structure:"
ls -la dist/