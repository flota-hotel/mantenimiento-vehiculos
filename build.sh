#!/bin/bash
# Build script for Cloudflare Pages deployment

echo "🚀 Preparing Vehicular System for deployment..."

# Clean previous build
rm -rf dist/
mkdir -p dist

# Copy main HTML file (the application)
cp index.html dist/ 2>/dev/null || echo "Warning: No index.html found"

# Copy static directories if they exist
if [ -d "static" ]; then
    cp -r static/ dist/static/ 2>/dev/null || echo "No static directory to copy"
fi

# Copy Cloudflare Pages configuration files
cp _headers dist/_headers 2>/dev/null || echo "No _headers file found"
cp _redirects dist/_redirects 2>/dev/null || echo "No _redirects file found"

# Copy functions directory for Cloudflare Pages Functions
if [ -d "functions" ]; then
    cp -r functions/ dist/functions/ 2>/dev/null || echo "No functions directory"
fi

echo "✅ Build completed successfully!"
echo "📁 Build output:"
ls -la dist/ 2>/dev/null || echo "Build directory created"

# Show file sizes for verification
echo "📊 File sizes:"
find dist/ -type f -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' || echo "Files ready for deployment"