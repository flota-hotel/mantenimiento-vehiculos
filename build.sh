#!/bin/bash
# Simple build script for Cloudflare Pages

echo "🚀 Building Sistema Vehicular..."

# Clean and create dist directory
rm -rf dist/
mkdir -p dist

# Copy main files
cp index.html dist/
cp manifest.webmanifest dist/
cp sw.js dist/

echo "✅ Build completed!"
echo "📁 Files ready in dist/:"
ls -la dist/