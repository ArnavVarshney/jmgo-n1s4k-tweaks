#!/usr/bin/env python3
"""Query Magisk's sqlite DB on the projector (no hardcoded IP).

Usage:
    python magisk_sql.py --device 192.168.X.X:5555 "SELECT * FROM settings;"
    python magisk_sql.py --device 192.168.X.X:5555 "SELECT * FROM policies;"

Requires root via /system/xbin/su (full path — bare su hits the Magisk
applet and denies without a policy row).
"""
import argparse
import shutil
import subprocess
import sys

SU = "/system/xbin/su"
MAGISK = "/debug_ramdisk/magisk"


def resolve_adb(user_adb):
    if user_adb:
        return user_adb
    found = shutil.which("adb")
    if found:
        return found
    # Windows fallback next to this script's parent checkout
    return "adb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", required=True, help="e.g. 192.168.51.74:5555")
    ap.add_argument("--adb", default=None)
    ap.add_argument("sql", nargs="?", default="SELECT * FROM settings;")
    args = ap.parse_args()

    adb = resolve_adb(args.adb)
    # Remote shell treats the double-quoted arg as one SQL string.
    cmd = [adb, "-s", args.device, "shell", SU, MAGISK,
           "--sqlite", '"' + args.sql + '"']
    print("RUN:", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print("RC:", r.returncode)
    print("OUT:", r.stdout)
    print("ERR:", r.stderr, file=sys.stderr)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
