#!/usr/bin/env python3
"""Enable Projectivy accessibility + notification listener (standalone).

`settings put` is BLOCKED for these keys on this box, so edit
/data/system/users/0/settings_secure.xml as root, preserve owner
system:system mode 600, then reboot.

Usage:
    python secedit_apply.py --device 192.168.X.X:5555 [--check] [--reboot]
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import os

SU = "/system/xbin/su"
SECURE_XML = "/data/system/users/0/settings_secure.xml"
A11Y = ("com.jmgo.hippo/com.jmgo.middleware.service.JmgoKeyAccessibilityService"
        ":com.spocky.projengmenu/.services.ProjectivyAccessibilityService")
NOTIF = "com.spocky.projengmenu/.services.notification.NotificationListener"


def adb_cmd(adb, device, *args):
    return [adb, "-s", device] + list(args)


def run(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", required=True)
    ap.add_argument("--adb", default=None)
    ap.add_argument("--check", action="store_true",
                    help="report only, change nothing")
    ap.add_argument("--reboot", action="store_true",
                    help="reboot if the file changed (needed to take effect)")
    args = ap.parse_args()
    adb = args.adb or shutil.which("adb") or "adb"

    r = run(adb_cmd(adb, args.device, "shell", SU, "cat", SECURE_XML))
    xml = r.stdout.decode("utf-8", errors="replace")
    if not xml or "<settings" not in xml:
        print("failed to read", SECURE_XML)
        print(r.stdout.decode(errors="replace")[:500])
        print(r.stderr.decode(errors="replace")[:500])
        sys.exit(1)

    xml2, n1 = re.subn(r'(name="enabled_accessibility_services" value=")[^"]*(")',
                       r"\g<1>%s\g<2>" % A11Y, xml)
    print("a11y replaced:", n1)
    if 'name="accessibility_enabled"' in xml2:
        xml2, n1b = re.subn(r'(name="accessibility_enabled" value=")[^"]*(")',
                            r"\g<1>1\g<2>", xml2)
        print("a11y_enabled set:", n1b)
    else:
        xml2 = xml2.replace(
            "</settings>",
            '  <setting id="9001" name="accessibility_enabled" value="1" package="android" />\n</settings>')
        print("a11y_enabled inserted")

    if 'name="enabled_notification_listeners"' in xml2:
        xml2, n2 = re.subn(r'(name="enabled_notification_listeners" value=")[^"]*(")',
                           r"\g<1>%s\g<2>" % NOTIF, xml2)
        print("notif replaced:", n2)
    else:
        xml2 = xml2.replace(
            "</settings>",
            '  <setting id="9002" name="enabled_notification_listeners" value="%s" package="android" />\n</settings>' % NOTIF)
        print("notif inserted")

    if xml2 == xml:
        print("already correct, nothing to do")
        return

    if args.check:
        print("would change settings_secure.xml (use without --check to apply)")
        return

    # Push via temp file (avoids quote-layer mangling through su/jsu).
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False,
                                     encoding="utf-8", newline="\n") as f:
        f.write(xml2)
        local = f.name
    try:
        remote = "/data/local/tmp/settings_secure.new.xml"
        r = run([adb, "-s", args.device, "push", local, remote])
        print(r.stdout.decode(errors="replace")[-500:])
        # install with correct owner/mode as root in one remote script
        script = ("cp %s %s && chown system:system %s && chmod 600 %s && echo OK"
                  % (remote, SECURE_XML, SECURE_XML, SECURE_XML))
        r = run(adb_cmd(adb, args.device, "shell", SU, "sh", "-c", script))
        out = r.stdout.decode(errors="replace")
        print(out[-500:])
        if "OK" not in out:
            print("install failed"); sys.exit(1)
        print("installed, owner/mode preserved")
    finally:
        os.unlink(local)

    if args.reboot:
        print("rebooting…")
        run(adb_cmd(adb, args.device, "shell", SU, "reboot"))


if __name__ == "__main__":
    main()
