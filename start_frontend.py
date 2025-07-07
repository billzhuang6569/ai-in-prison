#!/usr/bin/env python3
"""
Startup script for Project Prometheus frontend
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install Node.js dependencies"""
    print("Installing Node.js dependencies...")
    try:
        os.chdir("frontend")
        subprocess.check_call(["npm", "install"])
        print("✓ Node.js dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        print("Make sure Node.js and npm are installed on your system")
        return False
    except FileNotFoundError:
        print("✗ npm not found. Please install Node.js and npm first")
        print("Download from: https://nodejs.org/")
        return False

def start_frontend():
    """Start the React development server"""
    print("Starting Project Prometheus frontend...")
    print("Frontend will be available at: http://localhost:24682")
    print("\nPress Ctrl+C to stop the frontend\n")
    
    try:
        subprocess.call(["npm", "start"])
    except KeyboardInterrupt:
        print("\n✓ Frontend stopped by user")
    except Exception as e:
        print(f"✗ Frontend error: {e}")

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    
    print("=" * 50)
    print("Project Prometheus - Frontend Development Server")
    print("=" * 50)
    
    # Check if frontend directory exists
    if not os.path.exists("frontend"):
        print("✗ Frontend directory not found!")
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start frontend
    start_frontend()

if __name__ == "__main__":
    main()