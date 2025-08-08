#!/usr/bin/env python3
"""
Setup script for creating Python virtual environment for NanoSimLab.

This script automates the creation of a virtual environment and installation
of all dependencies for development.
"""

import os
import subprocess
import sys
import venv
from pathlib import Path


def run_command(cmd, check=True, cwd=None):
    """Run a shell command and print output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def create_venv(venv_path):
    """Create virtual environment."""
    print(f"Creating virtual environment at {venv_path}")
    venv.create(venv_path, with_pip=True, clear=True)


def get_pip_path(venv_path):
    """Get path to pip in virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def get_python_path(venv_path):
    """Get path to python in virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def main():
    """Main setup function."""
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"

    print("Setting up NanoSimLab development environment...")

    # Create virtual environment
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        response = input("Recreate it? (y/N): ").lower()
        if response != 'y':
            print("Using existing virtual environment.")
        else:
            import shutil
            shutil.rmtree(venv_path)
            create_venv(venv_path)
    else:
        create_venv(venv_path)

    # Get paths
    pip_path = get_pip_path(venv_path)
    python_path = get_python_path(venv_path)

    # Upgrade pip
    run_command([str(pip_path), "install", "--upgrade", "pip"])

    # Install package in development mode with all dependencies
    print("Installing NanoSimLab in development mode...")
    run_command([
        str(pip_path), "install", "-e", ".[dev,analysis,viz,molsim,builder]"
    ], cwd=project_root)

    # Install pre-commit hooks if available
    try:
        run_command([str(python_path), "-m", "pre_commit", "install"],
                   cwd=project_root, check=False)
        print("Pre-commit hooks installed.")
    except Exception:
        print("Pre-commit not available, skipping hooks setup.")

    # Run basic tests to verify installation
    print("Running basic tests to verify installation...")
    try:
        run_command([str(python_path), "-m", "pytest", "tests/test_basic.py", "-v"],
                   cwd=project_root)
        print("✅ Installation verified successfully!")
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed, but installation is complete.")

    # Print activation instructions
    print("\n" + "="*60)
    print("Setup complete! To activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  {venv_path / 'Scripts' / 'activate.bat'}")
    else:
        print(f"  source {venv_path / 'bin' / 'activate'}")

    print("\nThen you can use:")
    print("  nanosim simulate --help")
    print("  pytest tests/")
    print("  python -c 'import nanosimlab; print(nanosimlab.__version__)'")
    print("="*60)


if __name__ == "__main__":
    main()
