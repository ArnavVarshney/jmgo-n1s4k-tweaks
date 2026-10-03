#!/usr/bin/env python3
"""Binary-safe screencap (adb shell mangles 0A->0D0A, so use exec-out).

Usage:
    python shot.py --device 192.168.X.X:5555 --out screen.png
"""
import argparse
import shutil
import subprocess

JMGO_PREFIX = b"Init wrapper sys mutex"


def resolve_adb(user_adb):
    if user_adb:
        return user_adb
    return shutil.which("adb") or "adb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", required=True)
    ap.add_argument("--adb", default=None)
    ap.add_argument("--out", default="screen.png")
    args = ap.parse_args()

    adb = resolve_adb(args.adb)
    r = subprocess.run([adb, "-s", args.device, "exec-out", "screencap -p"],
                       capture_output=True, timeout=60)
    d = r.stdout
    # JMGO prepends a 46-byte wrapper line before the PNG on some builds.
    i = d.find(b"\x89PNG")
    print("png at", i, "total", len(d))
    blob = d[i:] if i >= 0 else d
    with open(args.out, "wb") as f:
        f.write(blob)
    print("saved", args.out)


if __name__ == "__main__":
    main()
