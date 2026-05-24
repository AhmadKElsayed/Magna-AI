import subprocess
import sys
import os
import signal

def main():
    print("Starting Magna AI Suite...")
    
    # Start backend
    print("--> Starting FastAPI backend...")
    backend_process = subprocess.Popen(
        ["uv", "run", "uvicorn", "main:app", "--reload"],
        cwd="backend",
        shell=True
    )
    
    # Start frontend
    print("--> Starting Next.js frontend...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        shell=True
    )
    
    def signal_handler(sig, frame):
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
