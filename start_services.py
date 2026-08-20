"""
ConsensusDev — Multi-Service Orchestrator & Launcher
Starts all 5 backend microservices + React Frontend concurrently.

Services:
  1. Gateway (Port 8000): Central Orchestration, GitHub Webhooks & REST API
  2. AI Engine (Port 8001): Multi-Agent LLM Review & Consensus
  3. Security Scanner (Port 8002): Checkov & Trivy Dual Scanner
  4. QA Runner (Port 8003): Automated Test & Mutation Analyzer
  5. Portal & Docs (Port 8004): DORA Metrics & Documentation
  6. React Frontend (Port 3000): Vite React + TypeScript Dashboard
"""

import os
import sys
import time
import subprocess
import signal
import urllib.request
import urllib.error
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = str(ROOT_DIR / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = str(ROOT_DIR / "venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

SERVICES = [
    {
        "name": "Gateway Service",
        "port": 8000,
        "health_url": "http://localhost:8000/health",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "AI Engine Service",
        "port": 8001,
        "health_url": "http://localhost:8001/health",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "ai_engine.main:app", "--host", "0.0.0.0", "--port", "8001"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "Security Scanner",
        "port": 8002,
        "health_url": "http://localhost:8002/health",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "scanners.main:app", "--host", "0.0.0.0", "--port", "8002"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "QA Runner Service",
        "port": 8003,
        "health_url": "http://localhost:8003/health",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "qa_runner.main:app", "--host", "0.0.0.0", "--port", "8003"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "Portal & Docs Service",
        "port": 8004,
        "health_url": "http://localhost:8004/health",
        "cmd": [PYTHON_EXE, "-m", "uvicorn", "portal.main:app", "--host", "0.0.0.0", "--port", "8004"],
        "cwd": ROOT_DIR,
    },
    {
        "name": "React Frontend",
        "port": 3000,
        "health_url": "http://localhost:3000/",
        "cmd": ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"],
        "cwd": ROOT_DIR / "frontend",
        "shell": True,
    },
]


def check_health(url: str, timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ConsensusDev-Launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in [200, 201]
    except Exception:
        return False


def main():
    print("=" * 70)
    print(" 🚀 STARTING CONSENSUS DEV MICROSERVICES PLATFORM (6 SERVICES)")
    print("=" * 70)

    # Initialize SQLite database and seed default admin user
    print("[*] Initializing SQLite database & Admin credentials...")
    try:
        subprocess.run([PYTHON_EXE, "-m", "gateway.seed_admin"], cwd=ROOT_DIR, check=False)
    except Exception as e:
        print(f"[-] Warning during admin seeding: {e}")

    processes = []

    try:
        for s in SERVICES:
            print(f"[*] Starting {s['name']} on port {s['port']}...")
            p = subprocess.Popen(
                s["cmd"],
                cwd=s["cwd"],
                shell=s.get("shell", False),
            )
            processes.append((s["name"], p, s["health_url"], s["port"]))
            time.sleep(0.5)

        print("\n[*] Waiting for microservices health checks...")
        time.sleep(2.0)

        all_ready = True
        for name, p, health_url, port in processes:
            healthy = False
            for _ in range(10):
                if check_health(health_url, timeout=1.0):
                    healthy = True
                    break
                time.sleep(0.5)

            if healthy:
                print(f"  [OK] {name:<26} (Port {port}) -> ONLINE")
            else:
                print(f"  [--] {name:<26} (Port {port}) -> STARTING / BACKGROUND")

        print("\n" + "=" * 70)
        print(" ✅ CONSENSUS DEV SYSTEM READY:")
        print("  - Frontend UI:        http://localhost:3000/")
        print("  - Gateway REST API:   http://localhost:8000/")
        print("  - AI Consensus Engine: http://localhost:8001/")
        print("  - Security Scanner:   http://localhost:8002/")
        print("  - QA Test Runner:     http://localhost:8003/")
        print("  - Portal & Docs:      http://localhost:8004/")
        print("=" * 70)
        print(" Press Ctrl+C to stop all services.\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Stopping all services...")
        for name, p, _, _ in processes:
            print(f"[*] Terminating {name}...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("[✓] All services stopped cleanly.")


if __name__ == "__main__":
    main()
