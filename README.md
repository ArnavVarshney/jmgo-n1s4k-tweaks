# JMGO N1S 4K (China, K310) — tweaks pack

Plug-and-play setup for the JMGO N1S 4K China edition (`K310`, Android 11,
firmware `1.1.31.23`) in Hong Kong, English UI.

Root is done separately with `jmgo_root.py` (see §1). Everything in this repo
is the layer **on top of root**: English settings, Projectivy launcher,
debloat, Magisk/Aurora config, locale/timezone/DNS.

> Last verified on-device: 2026-10-02. Device: 32-bit ARM (`armeabi-v7a`,
> MT9671), 64 GB, userdebug, SELinux permissive, `verifiedbootstate=orange`,
> no vbmeta, dynamic partitions, no fastboot, USB host-only (no USB adb).

## 1. Root first (one time)

`scripts/` in this repo assumes root already works:

```powershell
$env:PYTHONUTF8="1"
python jmgo_root.py <PROJECTOR_IP>   # full exploit, see root/README
.\adb.exe -s <IP>:5555 shell "/system/xbin/su id"   # expect uid=0
```

- Always use the FULL path `/system/xbin/su`. Bare `su` hits
  `/system/bin/su` (Magisk applet, denies without a policy row).
- `/system` is dm-verity read-only — cannot remount rw. Bind-mounts work.
- Backdoor (root restore): `/vendor/factory/bin/factory_clt 4 '<sh>'`
  runs as root, no auth, arg < 256 chars. If it stops working:
  `setprop ctl.start factory_svc`.
- `adb root` never elevates on this box. Recovery has no network adb.
- After an official reflash `/system` is pristine: re-run `jmgo_root.py`,
  then re-apply §3. If the script dies at byte-verify, the new firmware
  patched the vuln — do NOT force it.

Root source lives outside this repo (large exploit + backups). This repo
starts after `uid=0` works.

## 2. Quick start — full tweak pack

```powershell
$env:PYTHONUTF8="1"
# find the projector if DHCP moved it
python scripts/find_projector.py
# apply everything (idempotent, safe to re-run)
python scripts/apply_tweaks.py --device 192.168.X.X:5555
# optional: English settings APK bind (needs --apk, see §4)
python scripts/apply_tweaks.py --device 192.168.X.X:5555 --en-apk C:\path\to\en_setting.apk
```

What it does (in order, each step skippable with `--skip <name>`):

1. `prereqs` — `adb connect`, check `/system/xbin/su id` = uid 0
2. `locale` — timezone `Asia/Hong_Kong`, `device_name='JMGO N1S 4K'`,
   Private DNS OFF
3. `debloat` — `pm disable-user` on: appstore, ai.voice, arwen,
   gamecenter, bajintech.assistant, helpcenter, pinyin, miot, music,
   os.guide (launcher handled separately)
4. `launcher` — install Projectivy if APK supplied, freeze
   `com.jmgo.launcher`, `cmd package set-home-activity`,
   fix HOME role holders (TV Bro steals HOME on install, so this runs last)
5. `magisk` — verify `zygisk=0`, list `policies` table (Aurora ALLOW)
6. `aurora` — set `PREFERENCE_INSTALLER_ID=2` (Root installer) in
   Aurora's shared_prefs, fix owner/mode
7. `a11y` — enable Projectivy accessibility + notification listener via
   `/data/system/users/0/settings_secure.xml` edit (the `settings put`
   provider blocks these keys), preserve `system:system` 600, reboot
   if changed
8. `ensettings` — push EN APK to `/data/local/tmp/en_setting.apk`,
   install `service.d/zz-en-settings.sh` to `/data/adb/service.d/`,
   live bind-mount + `am force-stop com.jmgo.setting.x`

Run with `--check` for a dry-run report without changing anything.

## 3. Current known-good state (2026-10-02)

- `magiskd` headless, manager app uninstalled, Zygisk OFF, `policies` =
  Aurora ALLOW only (uid 10051).
- `service.d/`: `zz-en-settings.sh` (bind), `zz-fix-su.sh` (harmless
  verity no-op), `00-test.sh` (boot probe).
- Settings bind active. Pristine settings APK md5 `c97345d7…`.
- Disabled (see above + `com.jmgo.launcher` frozen for Projectivy;
  `pm enable` to revert). Uninstalled: rootfix.doctor, LSPosed mgr,
  Magisk mgr, FlixVision, morelocale. `com.jmgo.update` is protected —
  keep declining OTAs.
- Installed: Projectivy 4.71 (HOME, a11y + notif listener; onboarding
  taps pending user), Aurora (Root installer id=2, silent installs),
  TV Bro, ExecCmd (keep), VLC/YouTube (stock). Plex never installed —
  install via Aurora.
- tz `Asia/Hong_Kong`, locale en-US, Private DNS OFF.

Full detail: `docs/STATE.md`. What NOT to try: `docs/PROVEN_BROKEN.md`.

## 4. English settings APK

The built APK (`~50 MB`, re-signed) is **not** committed (GitHub file +
repo-size hygiene). Build it yourself or attach it to a GitHub Release and
pass `--en-apk`:

```
settings-i18n/           validated EN strings (committed)
  overlay_en_strings.xml  full values-zh-rCN map, placeholders preserved
  en_arrays.xml           arrays
docs/SETTINGS_I18N.md     rebuild pipeline (apktool + zipalign)
```

Pipeline summary: patch `setting_dec/res/values-zh-rCN/strings.xml` by NAME
from validated map → `apktool b` → `zipalign -f -p 4` → bind-mount live
(never bind before PMS boot scan — it unregisters `com.jmgo.setting.x`,
see `docs/PROVEN_BROKEN.md`).

The app forces `zh-rCN` internally; the EN build has zero Chinese left.
Leftover Chinese elsewhere (launcher tiles, hardcoded layouts) belongs to
other packages — out of scope, screenshot-driven per screen.

Live bind is always safe; the boot script MUST wait for `sys.boot_completed`
(+15 s), then bind + `am force-stop`.

## 5. Repo layout

```
README.md
docs/STATE.md docs/PROVEN_BROKEN.md docs/RECOVERY.md docs/FIRMWARE.md docs/SETTINGS_I18N.md
scripts/apply_tweaks.py      # full pack, idempotent
scripts/find_projector.py    # subnet sweep for :5555
scripts/magisk_sql.py        # query Magisk db (no hardcoded IP)
scripts/secedit_apply.py     # a11y/notif fix standalone
scripts/shot.py              # binary-safe screencap
service.d/zz-en-settings.sh service.d/zz-fix-su.sh
settings-i18n/*.xml
apk-source/                  # ExecCmd source + build notes (tiny app)
```

Windows/PowerShell gotchas: `$env:PYTHONUTF8="1"` for every python call,
never `>`-redirect adb binary output (use `shot.py` / `exec-out`), no
`grep/sed/head` (use `Select-String`), `adb shell` mangles binary
(`0A→0D0A`), quote-heavy remote commands fail via `su` re-splitting —
push a script file and run it instead. `input tap` is 1920x1080; verify
with screenshots.

## 6. Security notes

- `/vendor/factory/bin/factory_clt` is an unauthenticated root backdoor.
  Any app can use it. Avoid shady APKs.
- Widevine CDM won't instantiate (`UnsupportedSchemeException`).
  Netflix/Disney/Prime need a certified stick. No fix in this repo.
- Keep declining OTAs — an OTA may patch the vuln and wipe `/data`.

## License

Security research for your own hardware. Use at your own risk.
