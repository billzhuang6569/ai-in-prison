#!/usr/bin/env python3
"""
Project Chimera Server Launcher

This script provides different modes for running the server:
- Development mode: With auto-reload for code changes
- Production mode: Stable server without file watching
"""

import argparse
import uvicorn
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Project Chimera Server")
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="Run in development mode with auto-reload"
    )
    parser.add_argument(
        "--host", 
        default=Config.HOST, 
        help="Host to bind to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=Config.PORT, 
        help="Port to bind to"
    )
    
    args = parser.parse_args()
    
    try:
        Config.validate()
        
        if args.dev:
            print(f"🚀 Starting Project Chimera in DEVELOPMENT mode on {args.host}:{args.port}")
            print("📁 Auto-reload enabled - server will restart on code changes")
            uvicorn.run(
                "main:app",
                host=args.host,
                port=args.port,
                reload=True,
                reload_excludes=["venv/*", "logs/*", "frontend/*", "__pycache__/*"],
                log_level="info"
            )
        else:
            print(f"🚀 Starting Project Chimera in PRODUCTION mode on {args.host}:{args.port}")
            print("🔒 Auto-reload disabled - stable server mode")
            uvicorn.run(
                "main:app",
                host=args.host,
                port=args.port,
                reload=False,
                log_level="info"
            )
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Please check your configuration and ensure OPENROUTER_API_KEY is set in .env file")

if __name__ == "__main__":
    main()