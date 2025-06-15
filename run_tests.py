#!/usr/bin/env python
"""Wrapper script to run pytest."""
import sys
import subprocess

def main():
    """Run pytest with all provided arguments."""
    return subprocess.call(["pytest"] + sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())