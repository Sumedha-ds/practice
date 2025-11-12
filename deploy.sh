#!/bin/bash
# Deployment script for Vercel
# This script prepares the project for Vercel deployment

echo "🚀 Preparing project for Vercel deployment..."

# Backup original requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "📦 Backing up original requirements.txt..."
    cp requirements.txt requirements-desktop.txt.bak
fi

# Copy requirements-vercel.txt to requirements.txt
if [ -f "requirements-vercel.txt" ]; then
    echo "📦 Using requirements-vercel.txt for deployment..."
    cp requirements-vercel.txt requirements.txt
    echo "✅ requirements.txt updated for Vercel"
else
    echo "❌ Error: requirements-vercel.txt not found!"
    exit 1
fi

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
if [ "$1" == "--prod" ]; then
    vercel --prod
else
    vercel
fi

# Restore original requirements.txt if backup exists
if [ -f "requirements-desktop.txt.bak" ]; then
    echo "🔄 Restoring original requirements.txt..."
    mv requirements-desktop.txt.bak requirements.txt
    echo "✅ requirements.txt restored"
fi

echo "✅ Deployment complete!"

