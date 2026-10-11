#!/usr/bin/env python3
"""Heal an orphaned Projectivy accessibility bind without rebooting.

Background: when Projectivy's process dies while its accessibility service
is bound (app update, force-stop, deep mem-sleep), the system parks it in
the accessibility "crashed services" list and never rebinds it. The UI then
shows enabled-but-not-running plus a persistent prompt. This box has no
accessibility settings screen at all (JMGO stripped it) and `settings put`
on the services list is silently ignored, so the only stock heal is a
reboot. Reinstalling the *same* APKs goes through the package-update path,
which rebuilds service state fresh and clears the flag — no data loss,
no reboot.

Usage:
    python heal_a11y.py --device 192.168.X.X:5555 [--check]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROJ = "com.spocky.projengmenu"
PROJ_SERVICE = ("com.spocky.projengmenu/"
                "com.spocky.projengmenu.services.ProjectivyAccessibilityService")


def run(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


class Ctx:
    def __init__(self, adb, device):
        self.adb = adb
        self.device = device

    def base(self, *args):
        return [self.adb, "-s", self.device] + list(args)

    def shell(self, cmd, timeout=60):
        r = run(self.base("shell", cmd), timeout=timeout)
        return r.stdout.decode("utf-8", errors="replace").strip()

    def state(self):
        return self.shell(
            "dumpsys accessibility | grep -i -E"
            " 'bound services|enabled services|crashed'")

    def bound_labels(self):
        return self.shell(
            "dumpsys accessibility | grep -i -o 'label=[a-zA-Z]*'")


def needs_heal(c):
    st = c.state()
    crashed_line = next((l for l in st.splitlines() if "rashed" in l), "")
    crashed = PROJ_SERVICE in crashed_line
    bound = "label=Projectivy" in c.bound_labels()
    return crashed or not bound, st, bound


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", required=True)
    ap.add_argument("--adb", default=None)
    ap.add_argument("--check", action="store_true",
                    help="report only, change nothing")
    ap.add_argument("--wait", type=int, default=90,
                    help="seconds to wait for rebind (default 90)")
    args = ap.parse_args()
    adb = args.adb or shutil.which("adb") or "adb"
    c = Ctx(adb, args.device)

    need, st, bound = needs_heal(c)
    print(st[:900])
    print("projectivy bound:", bound)
    if not need:
        print("healthy, nothing to do")
        return

    if args.check:
        print("would heal via same-version reinstall "
              "(re-run without --check to apply)")
        return

    paths = c.shell("pm path " + PROJ)
    apks = [l.split(":", 1)[1].strip() for l in paths.splitlines()
            if l.startswith("package:")]
    if not apks:
        print("cannot find installed APKs for " + PROJ)
        sys.exit(1)
    print("pulling %d APKs…" % len(apks))
    tmp = tempfile.mkdtemp(prefix="projfix")
    try:
        local = []
        for remote in apks:
            name = remote.rsplit("/", 1)[-1]
            dest = os.path.join(tmp, name)
            r = run(c.base("pull", remote, dest), timeout=300)
            if r.returncode != 0 or not os.path.exists(dest):
                print("pull failed: " + remote)
                sys.exit(1)
            local.append(dest)
        print("reinstalling same version…")
        r = run(c.base("install-multiple", "-r") + local, timeout=300)
        out = (r.stdout.decode(errors="replace")
               + r.stderr.decode(errors="replace"))
        print(out.strip()[-200:])
        if "Success" not in out:
            print("reinstall failed")
            sys.exit(1)
        print("waiting for rebind…")
        deadline = time.time() + args.wait
        while time.time() < deadline:
            time.sleep(10)
            if "label=Projectivy" in c.bound_labels():
                print("HEALED: Projectivy bound")
                print(c.state()[:900])
                return
            st2, bound2 = needs_heal(c)[1:]
            print("…not yet bound")
        print("TIMEOUT: still not bound. Final state:")
        print(c.state()[:900])
        sys.exit(1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
