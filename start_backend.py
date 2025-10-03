#!/usr/bin/env python3
"""
Script to start the backend server with proper CORS configuration.
"""

import subprocess
import sys
import os
from pathlib import Path

def start_backend():
    """Start the backend server with proper configuration"""
    
    print("🚀 Starting HR Pilot Backend Server...")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print(f"📁 Working directory: {project_dir}")
    print(f"🌐 Server will run on: http://localhost:3003")
    print(f"📚 API Documentation: http://localhost:3003/docs")
    print(f"🧪 CORS Test endpoint: http://localhost:3003/cors-test")
    print()
    
    # Check if virtual environment exists
    venv_path = project_dir / "venv"
    if venv_path.exists():
        print("✅ Virtual environment found")
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"  # Windows
    else:
        print("⚠️  Virtual environment not found, using system Python")
        python_path = "python"
    
    try:
        # Start the server
        print("🔄 Starting server...")
        cmd = [
            str(python_path), "-m", "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "3003",
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"🔧 Command: {' '.join(cmd)}")
        print()
        print("📝 Server logs:")
        print("-" * 50)
        
        # Run the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure you're in the correct directory")
        print("   2. Check if all dependencies are installed: pip install -r requirements.txt")
        print("   3. Verify the database is running")
        print("   4. Check if port 3003 is available")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_backend()
