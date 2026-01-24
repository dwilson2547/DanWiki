#!/usr/bin/env python3
"""
Display version information for Wiki Tagging Service.

Usage:
    python version.py
    python -m tagging_api.version
"""
import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

try:
    from __version__ import __version__, __changelog__
except ImportError:
    __version__ = "unknown"
    __changelog__ = "Version information not available"

try:
    from config import settings
    config_version = settings.version
except ImportError:
    config_version = "unknown"


def print_version():
    """Print version information."""
    print(f"Wiki Tagging Service v{__version__}")
    print(f"Config version: {config_version}")
    print()
    print("Recent changes:")
    print(__changelog__)


if __name__ == "__main__":
    print_version()
