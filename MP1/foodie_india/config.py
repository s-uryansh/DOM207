import os
from pathlib import Path


os.environ.setdefault("MPLCONFIGDIR", "/tmp/mp1-matplotlib")

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs"
FIGURES = OUTPUT / "figures"
DAY_ORDER = ["Thur", "Fri", "Sat", "Sun"]
TIME_ORDER = ["Lunch", "Dinner"]
COLORS = {
    "blue": "#2a6f97",
    "gold": "#d89b2b",
    "teal": "#3a9188",
    "red": "#b64b4b",
}
