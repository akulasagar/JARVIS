#!/usr/bin/env python3
"""
Railway Deployment Helper Script
This script helps prepare your Flask app for Railway deployment.
"""

import os
import subprocess
import sys
import secrets

def check_git_repo():
    """Check if we're in a git repository."""
    try:
        subprocess.run(['git', 'status'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_requirements():
    """Check if requirements.txt exists."""
    return os.path.exists('requirements.txt')

def check_procfile():
    """Check if Procfile exists."""
    return os.path.exists('Procfile')

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_hex(32)

def main():
    print("🚀 Railway Deployment Helper")
    print("=" * 40)
    
    # Check prerequisites
    print("\n1. Checking prerequisites...")
    
    if not check_git_repo():
        print("❌ Error: Not in a git repository!")
        print("   Please run: git init && git add . && git commit -m 'Initial commit'")
        return False
    
    if not check_requirements():
        print("❌ Error: requirements.txt not found!")
        return False
    
    if not check_procfile():
        print("❌ Error: Procfile not found!")
        return False
    
    print("✅ All prerequisites met!")
    
    # Generate secret key
    print("\n2. Generating secure secret key...")
    secret_key = generate_secret_key()
    print(f"✅ Generated secret key: {secret_key[:20]}...")
    
    # Instructions
    print("\n3. Deployment Instructions:")
    print("=" * 40)
    print("📋 Follow these steps to deploy:")
    print()
    print("1. Go to https://railway.app")
    print("2. Sign up with your GitHub account")
    print("3. Click 'New Project'")
    print("4. Select 'Deploy from GitHub repo'")
    print("5. Choose this repository")
    print("6. In the project settings, add these environment variables:")
    print()
    print(f"   GEMINI_API_KEY=your_actual_gemini_api_key_here")
    print(f"   SECRET_KEY={secret_key}")
    print()
    print("7. Railway will automatically deploy your app!")
    print()
    print("🔗 Your app will be available at: https://your-app-name.railway.app")
    print()
    print("📝 Important Notes:")
    print("- Replace 'your_actual_gemini_api_key_here' with your real Gemini API key")
    print("- Keep your API keys secure and never commit them to git")
    print("- The app will automatically restart when you push changes to GitHub")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 