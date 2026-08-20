"""
ConsensusDev — Multi-Service Orchestrator & Launcher
Starts all 4 ConsensusDev microservices + React Frontend concurrently.

Services:
  1. Gateway (Port 8000): Central Orchestration & GitHub Webhooks
  2. AI Engine (Port 8001): Multi-Agent LLM Review & Consensus
  3. Security Scanner (Port 8002): Checkov & Trivy Dual Scanner
  4. React Portal (Port 3000): Vite React + TypeScript Frontend
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = str(ROOT_DIR / "venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

SERVICES = [
    {
        "name": "Gateway Service",
        "port": 8000,
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "AI Engine Service",
        "port": 8001,
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "ai_engine.main:app", "--host", "0.0.0.0", "--port", "8001"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "Security Scanner",
        "port": 8002,
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "scanners.main:app", "--host", "0.0.0.0", "--port", "8002"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "React Frontend",
        "port": 3000,
        "cmd": ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"],
        "cwd": ROOT_DIR / "frontend",
        "shell": True,
    },
]


def main():
    print("=" * 65)
    print(" 🚀 STARTING CONSENSUS DEV MICROSERVICES PLATFORM")
    print("=" * 65)

    processes = []

    try:
        for s in SERVICES:
            print(f"[*] Starting {s['name']} on port {s['port']}...")
            p = subprocess.Popen(
                s["cmd"],
                cwd=s["cwd"],
                shell=s.get("shell", False),
            )
            processes.append((s["name"], p))
            time.sleep(1.0)

        print("\n" + "=" * 65)
        print(" ✅ ALL SERVICES RUNNING SUCCESSFULLY:")
        print("  - Frontend UI:        http://localhost:3000/")
        print("  - Gateway API:        http://localhost:8000/")
        print("  - AI Consensus Engine: http://localhost:8001/")
        print("  - Security Scanner:   http://localhost:8002/")
        print("=" * 65)
        print(" Press Ctrl+C to stop all services.\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Stopping all services...")
        for name, p in processes:
            print(f"[*] Terminating {name}...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("[✓] All services stopped cleanly.")


if __name__ == "__main__":
    main()
