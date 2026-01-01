#!/usr/bin/env python3
"""
OmniAgent - Run All Script
==========================
Setup, test, validate, and run OmniAgent.

Usage:
    python run_all.py              # Interactive menu
    python run_all.py setup        # Setup environment
    python run_all.py test         # Run tests
    python run_all.py validate     # Validate installation
    python run_all.py run          # Run application
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(cmd, description=None):
    """Run a shell command and return success status."""
    if description:
        print_info(description)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)

def setup_environment():
    """Setup Python environment and dependencies."""
    print_header("Setting Up Environment")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print_success(f"Python {python_version.major}.{python_version.minor} detected")
    else:
        print_error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    
    # Create virtual environment if not exists
    if not Path("venv").exists():
        print_info("Creating virtual environment...")
        success, _ = run_command("python -m venv venv")
        if success:
            print_success("Virtual environment created")
        else:
            print_warning("Could not create venv, continuing with system Python")
    
    # Install dependencies
    print_info("Installing dependencies...")
    success, output = run_command("pip install -r requirements.txt")
    if success:
        print_success("Dependencies installed")
    else:
        print_error(f"Failed to install dependencies: {output}")
        return False
    
    # Check for .env file
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print_info("Creating .env from .env.example...")
            import shutil
            shutil.copy(".env.example", ".env")
            print_success(".env file created")
            print_warning("Please edit .env and add your GROQ_API_KEY")
        else:
            print_warning("No .env file found - AI features will be disabled")
    else:
        print_success(".env file exists")
    
    print_success("Environment setup complete!")
    return True

def validate_installation():
    """Validate all components are working."""
    print_header("Validating Installation")
    
    errors = []
    
    # Check Python syntax of all files
    print_info("Checking Python syntax...")
    py_files = list(Path(".").rglob("*.py"))
    py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
    
    for f in py_files:
        success, _ = run_command(f"python -m py_compile {f}")
        if not success:
            errors.append(f"Syntax error in {f}")
    
    if not errors:
        print_success(f"All {len(py_files)} Python files have valid syntax")
    
    # Check imports
    print_info("Checking imports...")
    try:
        sys.path.insert(0, str(Path(".").absolute()))
        from core.config import Config
        print_success("core.config imports correctly")
        
        from core.analyzer import DataAnalyzer
        print_success("core.analyzer imports correctly")
        
        from mcp.protocol import MCPBus, MCPMessage
        print_success("mcp.protocol imports correctly")
        
    except ImportError as e:
        errors.append(f"Import error: {e}")
        print_error(f"Import error: {e}")
    
    # Check required directories
    print_info("Checking directories...")
    required_dirs = ["core", "agents", "mcp", "ui", "data"]
    for d in required_dirs:
        if Path(d).exists():
            print_success(f"Directory '{d}' exists")
        else:
            errors.append(f"Missing directory: {d}")
            print_error(f"Missing directory: {d}")
    
    # Check required files
    print_info("Checking required files...")
    required_files = ["app.py", "requirements.txt", "README.md"]
    for f in required_files:
        if Path(f).exists():
            print_success(f"File '{f}' exists")
        else:
            errors.append(f"Missing file: {f}")
            print_error(f"Missing file: {f}")
    
    # Summary
    if errors:
        print_error(f"\nValidation failed with {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print_success("\nAll validations passed!")
        return True

def run_tests():
    """Run test suite."""
    print_header("Running Tests")
    
    # Check if pytest is installed
    success, _ = run_command("python -c 'import pytest'")
    if not success:
        print_warning("pytest not installed, installing...")
        run_command("pip install pytest pytest-cov")
    
    # Run tests
    if Path("tests").exists():
        print_info("Running pytest...")
        success, output = run_command("python -m pytest -v")
        print(output)
        if success:
            print_success("All tests passed!")
        else:
            print_error("Some tests failed")
        return success
    else:
        print_warning("No tests directory found")
        return True

def run_application():
    """Run the Streamlit application."""
    print_header("Starting OmniAgent")
    
    print_info("Starting Streamlit server...")
    print_info("Access the application at: http://localhost:8501")
    print_info("Press Ctrl+C to stop\n")
    
    os.system("streamlit run app.py")

def show_menu():
    """Show interactive menu."""
    print_header("OmniAgent - Management Console")
    
    print("1. Setup Environment")
    print("2. Validate Installation")
    print("3. Run Tests")
    print("4. Run Application")
    print("5. Full Setup & Run (1+2+4)")
    print("6. Exit")
    print()
    
    choice = input("Select option (1-6): ").strip()
    
    if choice == "1":
        setup_environment()
    elif choice == "2":
        validate_installation()
    elif choice == "3":
        run_tests()
    elif choice == "4":
        run_application()
    elif choice == "5":
        if setup_environment():
            if validate_installation():
                run_application()
    elif choice == "6":
        print_info("Goodbye!")
        sys.exit(0)
    else:
        print_error("Invalid option")
    
    input("\nPress Enter to continue...")
    show_menu()

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            setup_environment()
        elif command == "validate":
            validate_installation()
        elif command == "test":
            run_tests()
        elif command == "run":
            run_application()
        elif command == "all":
            if setup_environment():
                if validate_installation():
                    run_application()
        else:
            print_error(f"Unknown command: {command}")
            print("Usage: python run_all.py [setup|validate|test|run|all]")
    else:
        show_menu()

if __name__ == "__main__":
    main()
