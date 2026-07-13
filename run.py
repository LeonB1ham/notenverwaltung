"""Reliable app launcher when editable .pth files are blocked on macOS."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notenverwaltung.app import main

if __name__ == "__main__":
    main()
