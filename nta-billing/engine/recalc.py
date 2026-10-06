"""Recalculate every formula in an .xlsx in place, then report Excel error
cells. openpyxl writes formulas without cached values - run this on every
file before reading numbers back or delivering.

Engine (config.RECALC_ENGINE, env NTA_RECALC):
  python       - built-in engine (xlcalc.py), no LibreOffice needed (default).
                 A formula it doesn't support falls back to LibreOffice if installed.
  libreoffice  - headless LibreOffice, the original method.

    python engine/recalc.py <file.xlsx> [timeout_seconds]
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import openpyxl

import config
from config import find_soffice

_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""

ERRORS = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A")


def recalc(path, timeout=120):
    if config.RECALC_ENGINE == "python":
        import xlcalc
        try:
            return xlcalc.recalc(path)
        except xlcalc.UnsupportedFormula as e:
            try:
                find_soffice()
            except FileNotFoundError:
                raise RuntimeError(f"{path}: {e}. Install LibreOffice and set NTA_RECALC=libreoffice")
            print(f"⚠ {e} - recalculating with LibreOffice", file=sys.stderr)
    return recalc_libreoffice(path, timeout)


def recalc_libreoffice(path, timeout=120):
    path = Path(path).resolve()
    soffice = find_soffice()
    with tempfile.TemporaryDirectory(prefix="nta-lo-") as prof:
        prof = Path(prof)
        url = prof.as_uri()
        subprocess.run([soffice, "--headless", "--terminate_after_init",
                        f"-env:UserInstallation={url}"], capture_output=True, timeout=timeout)
        mdir = prof / "user" / "basic" / "Standard"
        if not mdir.exists():
            raise RuntimeError("LibreOffice did not create a profile - is another LibreOffice window open?")
        (mdir / "Module1.xba").write_text(_MACRO, encoding="utf-8")
        before = path.stat().st_mtime_ns
        r = subprocess.run([soffice, "--headless", "--norestore", f"-env:UserInstallation={url}",
                            "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
                            str(path)], capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(f"LibreOffice failed: {r.stderr.strip()}")
        for _ in range(20):
            if path.stat().st_mtime_ns != before:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("LibreOffice did not rewrite the file (close any open LibreOffice/Excel copy of it and retry)")

    wb = openpyxl.load_workbook(path, data_only=True)
    errs = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value in ERRORS:
                    errs.append(f"{ws.title}!{c.coordinate}={c.value}")
    return {"status": "success" if not errs else "errors_found", "engine": "libreoffice",
            "total_errors": len(errs), "errors": errs[:50]}


def recalc_or_raise(path, timeout=120):
    res = recalc(path, timeout)
    if res["total_errors"]:
        raise RuntimeError(f"{path}: {res['total_errors']} formula errors, e.g. {res['errors'][:5]}")
    return res


if __name__ == "__main__":
    print(json.dumps(recalc(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 120),
                     ensure_ascii=False, indent=2))
