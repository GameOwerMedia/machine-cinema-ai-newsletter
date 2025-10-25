#!/usr/bin/env python3
"""Setup script for Machine Cinema AI Newsletter"""

import subprocess
import sys

def install_requirements():
    """Install required Python packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install requirements")
        sys.exit(1)

def test_modules():
    """Test if all modules can be imported"""
    try:
        from fetch_ai_news import gather, save_seen
        from make_posts import format_post
        print("[OK] All modules can be imported successfully")
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

if __name__ == "__main__":
    print("Setting up Machine Cinema AI Newsletter...")
    install_requirements()
    if test_modules():
        print("Setup completed successfully!")
        print("Run: python generate_all.py")
    else:
        print("Setup failed. Please check the requirements.")
