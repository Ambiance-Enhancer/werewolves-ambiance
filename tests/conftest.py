import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `src` package can be imported
ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)
