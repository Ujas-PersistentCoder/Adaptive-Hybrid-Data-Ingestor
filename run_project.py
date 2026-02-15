"""
Final running file for the project. Connects to the API, and once successsfully connected call the main.py to run the orchestrator that manages all other files
"""

import subprocess
import time
import sys
import requests

def wait_for_server(url, timeout=15):
    """Retries connecting to the server until it's ready or timeout hits."""
    start_time = time.time()
    print(f"⏳ Waiting for API at {url}...")
    while time.time() - start_time < timeout:
        try:
            # We just try to get a response from the base URL
            requests.get(url, timeout=1)
            print("✅ Server is UP and responding!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1) # Wait 1 second before retrying
    return False

def run_everything():
    print("🚀 Initializing Autonomous Ingestion System...")

    # 1. Start the API Server
    # Ensure 'app.py' is the correct name of your server file!
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 2. Wait for the server to actually respond
    if wait_for_server("http://127.0.0.1:8000"):
        try:
            # 3. Start the Main Pipeline
            subprocess.run([sys.executable, "main.py"])
        except KeyboardInterrupt:
            print("\nShutting down...")
    else:
        print("❌ Error: Server failed to start in time.")

    # 4. Cleanup
    print("🛑 Shutting down API Server...")
    server_process.terminate()

if __name__ == "__main__":
    run_everything()