#!/usr/bin/env python3
"""
Startup script for Project Prometheus backend
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    return True

def start_server():
    """Start the FastAPI server"""
    print("Starting Project Prometheus backend server...")
    print("Server will be available at: http://localhost:24861")
    print("WebSocket endpoint: ws://localhost:24861/ws")
    print("API docs: http://localhost:24861/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.call([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except Exception as e:
        print(f"✗ Server error: {e}")

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 50)
    print("Project Prometheus - AI Social Behavior Simulation")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Warning: .env file not found!")
        print("Please copy .env.example to .env and configure your OpenRouter API key")
        print("The system will work with random actions if no API key is provided.")
        print()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()