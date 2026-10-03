#!/usr/bin/env python3
"""JMGO N1S 4K (K310) — full tweak pack, idempotent plug-and-play.

Assumes root already works: /system/xbin/su id -> uid=0.
Run root step first (jmgo_root.py), then:

    python apply_tweaks.py --device 192.168.X.X:5555 [--check]
                           [--skip locale,debloat,launcher,magisk,aurora,a11y,ensettings]
                           [--en-apk /path/to/en_setting.apk]
                           [--projectivy-apk ...] [--aurora-apk ...] [--tvbro-apk ...]
                           [--grant-uid 10123] [--reboot]

Steps (in order):
  locale     tz Asia/Hong_Kong, device_name, Private DNS OFF
  debloat    pm disable-user on JMGO bloat (pattern-matched, never fatal)
  launcher   install supplied APKs, freeze com.jmgo.launcher,
             set-home-activity + HOME role -> Projectivy (runs AFTER
             installs: TV Bro steals HOME on install)
  magisk     verify zygisk=0 + show policies (read-only unless --grant-uid)
  aurora     PREFERENCE_INSTALLER_ID=2 (Root installer), owner/mode preserved
  a11y       accessibility + notification listener via settings_secure.xml
             edit (settings put is blocked), reboot needed
  ensettings push EN APK + service.d script, live bind + force-stop

--check reports what would change without changing anything.
Safe to re-run: every step checks current state first.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

SU = "/system/xbin/su"
PROJ_HOME = "com.spocky.projengmenu/.ui.home.MainActivity"
PROJ_PKG = "com.spocky.projengmenu"
TVBRO_PKG = "com.phlox.tvwebbrowser"
A11Y = ("com.jmgo.hippo/com.jmgo.middleware.service.JmgoKeyAccessibilityService"
        ":com.spocky.projengmenu/.services.ProjectivyAccessibilityService")
NOTIF = "com.spocky.projengmenu/.services.notification.NotificationListener"
SECURE_XML = "/data/system/users/0/settings_secure.xml"
EN_ORIG = "/system/system_ext/app/JmGOSetting_OS8.0/JmGOSetting_OS8.0.apk"
EN_TMP = "/data/local/tmp/en_setting.apk"

# substring patterns matched against `pm list packages` (lowercased).
# com.jmgo.launcher handled in launcher step, not here.
DEBLOAT_PATTERNS = [
    "com.jmgo.appstore",
    "com.jmgo.ai.voice",
    "com.jmgo.arwen",
    "gamecenter",
    "bajintech",
    "com.jmgo.helpcenter",
    "pinyin",
    "miot", "miiot",
    "com.jmgo.music", "jmgo.music",
    "os.guide",
]


def log(s=""):
    print(s, flush=True)


def run(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


class Ctx:
    def __init__(self, adb, device, check):
        self.adb = adb
        self.device = device
        self.check = check
        self.changed_a11y = False

    def base(self, *args):
        return [self.adb, "-s", self.device] + list(args)

    def shell(self, cmd, timeout=60):
        r = run(self.base("shell", cmd), timeout=timeout)
        return r.stdout.decode("utf-8", errors="replace").strip()

    def shell_su(self, remote, timeout=60):
        r = run(self.base("shell", SU, remote), timeout=timeout)
        return (r.stdout.decode("utf-8", errors="replace").strip(),
                r.stderr.decode("utf-8", errors="replace").strip(),
                r.returncode)

    def push(self, local, remote, timeout=120):
        r = run(self.base("push", local, remote), timeout=timeout)
        out = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return r.returncode == 0, out


def step_prereqs(c):
    log("== prereqs ==")
    r = run(c.base("connect", c.device), timeout=30)
    log(r.stdout.decode(errors="replace").strip()[-200:])
    out, err, _ = c.shell_su("id")
    log("su id: " + out)
    if "uid=0" not in out:
        log("FATAL: root not working. Re-run jmgo_root.py first. " + err)
        return False
    log("root OK")
    return True


def step_locale(c):
    log("== locale ==")
    cmds = [
        "setprop persist.sys.timezone Asia/Hong_Kong",
        "settings put global device_name 'JMGO N1S 4K'",
        "settings put global private_dns_mode off",
        "settings delete global private_dns_specifier",
    ]
    for cmd in cmds:
        if c.check:
            log("[check] would run: " + cmd)
        else:
            log("$ " + cmd + " -> " + c.shell(cmd)[:120])


def step_debloat(c):
    log("== debloat ==")
    pkgs = c.shell("pm list packages")
    installed = [l.split(":", 1)[1].strip() for l in pkgs.splitlines()
                 if l.startswith("package:")]
    low = {p.lower(): p for p in installed}
    targets = []
    for pat in DEBLOAT_PATTERNS:
        for lname, real in low.items():
            if pat in lname and real not in targets:
                targets.append(real)
    if not targets:
        log("no bloat matches found (already clean?)")
        return
    for pkg in targets:
        state = c.shell("dumpsys package %s | grep -m1 -i disabled" % pkg)
        if c.check:
            log("[check] would disable: %s (%s)" % (pkg, state[:80]))
        else:
            out = c.shell("pm disable-user --user 0 %s" % pkg)
            log("%s -> %s" % (pkg, out[:120]))


def install_apk(c, path, label):
    if not path:
        return
    if not os.path.exists(path):
        log("%s APK not found: %s (skipping)" % (label, path))
        return
    if c.check:
        log("[check] would install %s: %s" % (label, path))
        return
    log("installing %s ..." % label)
    r = run(c.base("install", "-r", path), timeout=300)
    out = r.stdout.decode(errors="replace")
    log(out[-300:])


def step_launcher(c):
    log("== launcher (Projectivy HOME) ==")
    if c.check:
        log("[check] would: freeze com.jmgo.launcher, set-home-activity %s, "
            "fix HOME role" % PROJ_HOME)
        return
    log(c.shell("pm disable-user --user 0 com.jmgo.launcher")[:120])
    log(c.shell("cmd package set-home-activity " + PROJ_HOME)[:160])
    # TV Bro steals HOME on install -> remove it, then assert Projectivy.
    log(c.shell("cmd role remove-role-holder android.app.role.HOME " + TVBRO_PKG)[:160])
    log(c.shell("cmd role add-role-holder android.app.role.HOME " + PROJ_PKG)[:160])
    cur = c.shell("dumpsys activity activities | grep -m1 mResumedActivity")
    log("resumed: " + cur[:200])
    log("verify with: python shot.py --device %s" % c.device)


def magisk_query(c, sql):
    out, err, _ = c.shell_su('/debug_ramdisk/magisk --sqlite "%s"' % sql)
    return out


def step_magisk(c, grant_uid):
    log("== magisk ==")
    z = magisk_query(c, "SELECT value FROM settings WHERE key='zygisk';")
    log("zygisk: " + z.strip() + ("  OK (must stay 0)" if "0" in z else "  WARNING: must be 0"))
    pol = magisk_query(c, "SELECT * FROM policies;")
    log("policies:\n" + pol[:1500])
    if grant_uid is not None:
        sql = "INSERT OR REPLACE INTO policies VALUES(%d,2,0,1,0);" % grant_uid
        if c.check:
            log("[check] would grant su: " + sql)
        else:
            log(magisk_query(c, sql)[:200])
            log("re-query:\n" + magisk_query(c, "SELECT * FROM policies;")[:1500])


def step_aurora(c):
    log("== aurora (Root installer id=2) ==")
    pref = "/data/data/com.aurora.store/shared_prefs/com.aurora.store_preferences.xml"
    stat, _, _ = c.shell_su("stat -c '%U %G %a' " + pref)
    log("owner: " + stat)
    if not stat or "No such file" in stat:
        log("aurora prefs not found (aurora not installed?)")
        return
    xml, _, _ = c.shell_su("cat " + pref)
    if "PREFERENCE_INSTALLER_ID" not in xml:
        log("installer key missing in prefs")
        return
    m = re.search(r'PREFERENCE_INSTALLER_ID" value="(\d)"', xml)
    log("current installer id: " + (m.group(1) if m else "?"))
    if m and m.group(1) == "2":
        log("already id=2")
        return
    if c.check:
        log("[check] would set PREFERENCE_INSTALLER_ID=2")
        return
    xml2, n = re.subn(r'(PREFERENCE_INSTALLER_ID" value=")\d(")', r"\g<1>2\g<2>", xml, count=1)
    log("replaced: %d" % n)
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False,
                                     encoding="utf-8", newline="\n") as f:
        f.write(xml2)
        local = f.name
    try:
        ok, out = c.push(local, "/data/local/tmp/aurora_prefs.xml")
        log(out[-300:])
        if not ok:
            log("push failed"); return
        user, grp = (stat.split() + ["u0_a51", "u0_a51"])[:2]
        script = ("cp /data/local/tmp/aurora_prefs.xml %s && chown %s:%s %s && chmod 660 %s"
                  " && am force-stop com.aurora.store && echo OK" % (pref, user, grp, pref, pref))
        out, err, _ = c.shell_su("sh -c '%s'" % script)
        log((out + err)[-300:])
    finally:
        os.unlink(local)


def step_a11y(c):
    log("== a11y ==")
    xml, _, _ = c.shell_su("cat " + SECURE_XML)
    if "<settings" not in xml:
        log("cannot read " + SECURE_XML); return
    xml2, n1 = re.subn(r'(name="enabled_accessibility_services" value=")[^"]*(")',
                       r"\g<1>%s\g<2>" % A11Y, xml)
    if 'name="accessibility_enabled"' in xml2:
        xml2, _ = re.subn(r'(name="accessibility_enabled" value=")[^"]*(")',
                          r"\g<1>1\g<2>", xml2)
    else:
        xml2 = xml2.replace("</settings>",
            '  <setting id="9001" name="accessibility_enabled" value="1" package="android" />\n</settings>')
    if 'name="enabled_notification_listeners"' in xml2:
        xml2, _ = re.subn(r'(name="enabled_notification_listeners" value=")[^"]*(")',
                          r"\g<1>%s\g<2>" % NOTIF, xml2)
    else:
        xml2 = xml2.replace("</settings>",
            '  <setting id="9002" name="enabled_notification_listeners" value="%s" package="android" />\n</settings>' % NOTIF)
    if xml2 == xml:
        log("already correct"); return
    log("a11y/notif needs update (replaced %d)" % n1)
    c.changed_a11y = True
    if c.check:
        log("[check] would rewrite " + SECURE_XML + " + reboot")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False,
                                     encoding="utf-8", newline="\n") as f:
        f.write(xml2)
        local = f.name
    try:
        ok, out = c.push(local, "/data/local/tmp/settings_secure.new.xml")
        log(out[-200:])
        if not ok:
            log("push failed"); return
        script = ("cp /data/local/tmp/settings_secure.new.xml %s && chown system:system %s"
                  " && chmod 600 %s && echo OK" % (SECURE_XML, SECURE_XML, SECURE_XML))
        out, err, _ = c.shell_su("sh -c '%s'" % script)
        log((out + err)[-300:])
    finally:
        os.unlink(local)


def step_ensettings(c, en_apk):
    log("== ensettings ==")
    here = os.path.dirname(os.path.abspath(__file__))
    svc = os.path.join(here, "..", "service.d", "zz-en-settings.sh")
    svc = os.path.normpath(svc)
    if en_apk:
        if not os.path.exists(en_apk):
            log("EN apk not found: " + en_apk); return
        if c.check:
            log("[check] would push %s -> %s + install service.d script + live bind"
                % (en_apk, EN_TMP))
            return
        ok, out = c.push(en_apk, EN_TMP)
        log(out[-300:])
        if not ok:
            log("EN apk push failed"); return
    else:
        present, _, _ = c.shell_su("ls -l " + EN_TMP)
        log("on-device EN apk: " + present[:160])
        if "No such file" in present:
            log("supply --en-apk to deploy (see docs/SETTINGS_I18N.md)")
    if os.path.exists(svc) and en_apk:
        ok, out = c.push(svc, "/data/local/tmp/zz-en-settings.sh")
        log(out[-200:])
        if ok:
            out, err, _ = c.shell_su(
                "cp /data/local/tmp/zz-en-settings.sh /data/adb/service.d/zz-en-settings.sh"
                " && chmod 755 /data/adb/service.d/zz-en-settings.sh && echo OK")
            log((out + err)[-200:])
    elif not os.path.exists(svc):
        log("service script missing in repo: " + svc)
    if c.check:
        log("[check] would live-bind + force-stop com.jmgo.setting.x")
        return
    if en_apk:
        out, err, _ = c.shell_su("mount -o bind %s %s && echo BIND_OK" % (EN_TMP, EN_ORIG))
        log((out + err)[-200:])
        log(c.shell("am force-stop com.jmgo.setting.x")[:120])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", required=True, help="e.g. 192.168.51.74:5555")
    ap.add_argument("--adb", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--skip", default="",
                    help="comma list: locale,debloat,launcher,magisk,aurora,a11y,ensettings")
    ap.add_argument("--en-apk", default=None)
    ap.add_argument("--projectivy-apk", default=None)
    ap.add_argument("--aurora-apk", default=None)
    ap.add_argument("--tvbro-apk", default=None)
    ap.add_argument("--grant-uid", type=int, default=None,
                    help="INSERT OR REPLACE su ALLOW row for uid (prompt UI never appears)")
    ap.add_argument("--reboot", action="store_true",
                    help="reboot at end if a11y changed")
    args = ap.parse_args()

    adb = args.adb or shutil.which("adb") or "adb"
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    c = Ctx(adb, args.device, args.check)
    log("device=%s check=%s skip=%s" % (args.device, args.check, sorted(skip)))

    if not step_prereqs(c):
        sys.exit(1)
    if "locale" not in skip:
        step_locale(c)
    if "debloat" not in skip:
        step_debloat(c)
    if "launcher" not in skip:
        install_apk(c, args.projectivy_apk, "projectivy")
        install_apk(c, args.aurora_apk, "aurora")
        install_apk(c, args.tvbro_apk, "tvbro")
        step_launcher(c)
    if "magisk" not in skip:
        step_magisk(c, args.grant_uid)
    if "aurora" not in skip:
        step_aurora(c)
    if "a11y" not in skip:
        step_a11y(c)
    if "ensettings" not in skip:
        step_ensettings(c, args.en_apk)

    log("")
    if c.check:
        log("CHECK done — nothing changed.")
    else:
        log("DONE.")
        if c.changed_a11y:
            if args.reboot:
                log("rebooting for a11y…")
                c.shell_su("reboot")
            else:
                log("NOTE: a11y changed — reboot to take effect.")


if __name__ == "__main__":
    main()
