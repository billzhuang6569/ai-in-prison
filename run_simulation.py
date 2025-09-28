#!/usr/bin/env python3
"""
Project Chimera - Quick Start Script

This script provides a simple way to run the simulation with different configurations.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import chromadb
        import requests
        import rich
        print("✓ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration is properly set up."""
    from config import Config
    
    try:
        Config.validate()
        print("✓ Configuration is valid")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("Please check your .env file and ensure OPENROUTER_API_KEY is set")
        return False

def run_backend():
    """Run the backend server."""
    print("Starting Project Chimera backend server...")
    
    if not check_dependencies():
        return False
    
    if not check_config():
        return False
    
    try:
        # Import and run the main server
        from main import app
        import uvicorn
        
        uvicorn.run(
            "main:app",
            host="localhost",
            port=8000,
            reload=True,
            log_level="info"
        )
        return True
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return False

def run_frontend():
    """Run the frontend development server."""
    frontend_dir = Path("frontend/chimera-frontend")
    
    if not frontend_dir.exists():
        print("Frontend directory not found. Please build the frontend first.")
        return False
    
    print("Starting frontend development server...")
    
    try:
        # Change to frontend directory and run npm dev
        os.chdir(frontend_dir)
        subprocess.run(["npm", "run", "dev"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to start frontend: {e}")
        return False
    except FileNotFoundError:
        print("npm not found. Please install Node.js and npm.")
        return False

def setup_environment():
    """Set up the environment for first-time users."""
    print("Setting up Project Chimera environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✓ Created .env file")
        print("Please edit .env file and set your OPENROUTER_API_KEY")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✓ Created logs directory")
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Python dependencies: {e}")
        return False
    
    # Install frontend dependencies if frontend exists
    frontend_dir = Path("frontend/chimera-frontend")
    if frontend_dir.exists():
        print("Installing frontend dependencies...")
        try:
            os.chdir(frontend_dir)
            subprocess.run(["npm", "install"], check=True)
            print("✓ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install frontend dependencies: {e}")
        except FileNotFoundError:
            print("npm not found. Please install Node.js to set up the frontend.")
    
    print("\nSetup complete! Next steps:")
    print("1. Edit .env file and set your OPENROUTER_API_KEY")
    print("2. Run: python run_simulation.py --backend")
    print("3. In another terminal, run: python run_simulation.py --frontend")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Project Chimera - AI Prison Simulation")
    parser.add_argument("--backend", action="store_true", help="Run backend server")
    parser.add_argument("--frontend", action="store_true", help="Run frontend development server")
    parser.add_argument("--setup", action="store_true", help="Set up environment for first-time use")
    parser.add_argument("--check", action="store_true", help="Check dependencies and configuration")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_environment()
    elif args.backend:
        run_backend()
    elif args.frontend:
        run_frontend()
    elif args.check:
        print("Checking Project Chimera setup...")
        deps_ok = check_dependencies()
        config_ok = check_config()
        
        if deps_ok and config_ok:
            print("\n✓ Everything looks good! You can start the simulation.")
        else:
            print("\n✗ Please fix the issues above before running the simulation.")
    else:
        print("Project Chimera - AI Stanford Prison Experiment Simulation")
        print("\nUsage:")
        print("  python run_simulation.py --setup     # First-time setup")
        print("  python run_simulation.py --check     # Check configuration")
        print("  python run_simulation.py --backend   # Run backend server")
        print("  python run_simulation.py --frontend  # Run frontend (in separate terminal)")
        print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()