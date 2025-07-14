#!/usr/bin/env python3
"""
Simple startup script for Vibe Shopping App
"""
import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def run_backend():
    """Run the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend stopped")
    except Exception as e:
        print(f"❌ Backend error: {e}")

def run_frontend():
    """Run the React frontend"""
    print("🌐 Starting React frontend...")
    os.chdir("frontend")
    try:
        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], check=True)
        
        # Start React dev server
        subprocess.run(["npm", "start"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped")
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        print("💡 Make sure Node.js and npm are installed")

def main():
    print("🛍️ Starting Vibe Shopping Application")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    try:
        # For now, just run the backend
        print("🎯 Running in backend-only mode")
        print("📡 API will be available at: http://localhost:8000")
        print("📚 API docs will be available at: http://localhost:8000/docs")
        print("\n💡 To test the API:")
        print("   curl -X POST http://localhost:8000/api/chat/start \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"initial_query\": \"red dress for party\"}'")
        print("\n🔄 Press Ctrl+C to stop")
        print("-" * 50)
        
        # Open browser to API docs
        time.sleep(2)
        webbrowser.open("http://localhost:8000/docs")
        
        run_backend()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
