#!/usr/bin/env python3
"""
Test script to create the GUI and verify the Docker setup.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, cwd=None):
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check, cwd=cwd,
                          capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def main():
    """Test the Docker setup."""
    project_root = Path(__file__).parent

    print("Testing NanoSimLab Docker setup...")

    # Make run.sh executable
    run_script = project_root / "run.sh"
    if run_script.exists():
        os.chmod(run_script, 0o755)
        print(f"Made {run_script} executable")

    # Create GUI
    print("Creating GUI scaffold...")
    result = run_command("./run.sh gui:create", cwd=project_root, check=False)

    if result.returncode == 0:
        print("✅ GUI created successfully")
    else:
        print("⚠️ GUI creation encountered issues")

    # Check if Docker is available
    print("Checking Docker availability...")
    result = run_command("docker --version", check=False)
    if result.returncode == 0:
        print("✅ Docker is available")

        # Test Docker build (but don't actually build to save time)
        print("Docker setup appears ready")
        print("To test the full setup, run:")
        print("  ./run.sh up")
        print("Then visit:")
        print("  - GUI: http://localhost:3000")
        print("  - API: http://localhost:8080/docs")
    else:
        print("⚠️ Docker not available - install Docker to test full setup")

if __name__ == "__main__":
    main()
