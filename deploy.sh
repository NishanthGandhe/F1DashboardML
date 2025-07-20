#!/bin/bash

# F1 Data Analysis Platform - Quick Deployment Script
# This script helps you deploy your app to various platforms

echo "🏁 F1 Data Analysis Platform - Deployment Helper"
echo "=================================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - F1 Analysis Platform"
fi

echo ""
echo "Choose your deployment option:"
echo "1. Streamlit Community Cloud (FREE - Recommended)"
echo "2. Heroku (Paid)"
echo "3. Railway (Easy Alternative)"
echo "4. Just prepare files (manual deployment)"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Preparing for Streamlit Community Cloud deployment..."
        echo ""
        echo "Steps to complete:"
        echo "1. Push your code to GitHub:"
        echo "   git remote add origin <your-github-repo-url>"
        echo "   git branch -M main"
        echo "   git push -u origin main"
        echo ""
        echo "2. Visit https://share.streamlit.io"
        echo "3. Connect your GitHub account"
        echo "4. Select this repository"
        echo "5. Choose 'app.py' as the main file"
        echo "6. Click Deploy!"
        echo ""
        echo "Your app will be live at: https://your-app-name.streamlit.app"
        ;;
    2)
        echo ""
        echo "🚀 Preparing for Heroku deployment..."
        echo ""
        echo "Make sure you have Heroku CLI installed, then run:"
        echo "heroku login"
        echo "heroku create your-f1-app-name"
        echo "git push heroku main"
        ;;
    3)
        echo ""
        echo "🚀 Preparing for Railway deployment..."
        echo ""
        echo "Steps:"
        echo "1. Visit https://railway.app"
        echo "2. Connect your GitHub account"
        echo "3. Select this repository"
        echo "4. Railway will auto-deploy!"
        ;;
    4)
        echo ""
        echo "✅ Deployment files created!"
        echo "All necessary files are ready for manual deployment."
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment preparation complete!"
echo "Your F1 Analysis Platform is ready to go live!"
