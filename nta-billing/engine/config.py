"""Paths and external tools. Everything is relative to the project folder,
so the whole folder can be moved/copied anywhere (Windows, Mac, Linux)."""
import os
import shutil
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"
ASSETS = ROOT / "assets"
ACCOUNTS = ROOT / "accounts"
OUTPUT = ROOT / "output"
INBOX = ROOT / "inbox"

TEMPLATE_DETAIL = ASSETS / "template_detail.xlsx"
TEMPLATE_NETA = ASSETS / "template_neta_format.xlsx"

DISCOUNT = 0.85      # הנחת קבלן 15%
OCCUPIED = 1.05      # תוספת דירה מאוכלסת 5%
VAT = 0.18

# Formula recalculation: "python" (built-in, default) or "libreoffice".
RECALC_ENGINE = os.environ.get("NTA_RECALC", "python").strip().lower()
if RECALC_ENGINE not in ("python", "libreoffice"):
    raise ValueError(f"NTA_RECALC must be 'python' or 'libreoffice', got {RECALC_ENGINE!r}")


def find_soffice():
    """LibreOffice executable. Override with env var NTA_SOFFICE."""
    env = os.environ.get("NTA_SOFFICE")
    if env and Path(env).exists():
        return env
    for name in ("soffice", "soffice.exe", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    candidates = []
    if platform.system() == "Windows":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            candidates.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")
    elif platform.system() == "Darwin":
        candidates.append(Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError(
        "LibreOffice (soffice) not found. Install LibreOffice, or set NTA_SOFFICE "
        "to the full path of soffice.exe")


def account_json(n):
    return ACCOUNTS / f"חשבון_{n}_נתונים.json"


def account_dir(n):
    d = OUTPUT / f"חשבון {n}"
    d.mkdir(parents=True, exist_ok=True)
    return d
