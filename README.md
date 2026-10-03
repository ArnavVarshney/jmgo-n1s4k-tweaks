# JMGO N1S 4K Tweaks

Configuration pack for the **JMGO N1S 4K China edition (K310, Android 11)**:
English system settings, Projectivy launcher setup, debloat, and
Magisk / Aurora / accessibility defaults — applied idempotently over ADB.

![platform](https://img.shields.io/badge/platform-Android%2011-green)
![arch](https://img.shields.io/badge/arch-armeabi--v7a-blue)
![python](https://img.shields.io/badge/python-3.8%2B-blue)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

> Tested against firmware `1.1.31.23`. Requires working root (see
> [Prerequisites](#prerequisites)). All operations are reversible unless
> noted.

## Features

| Area | What the pack does |
| ---- | ------------------ |
| Localization | Timezone, device name, Private DNS defaults |
| Debloat | Disables JMGO bundled apps (app store, voice assistant, guides, IoT, music, input method) via `pm disable-user` |
| Launcher | Freezes the stock launcher, sets Projectivy as HOME activity and HOME role holder |
| Root policy | Verifies Magisk Zygisk stays off; optional `--grant-uid` for silent `su` grants (the on-TV prompt never appears) |
| App installer | Sets Aurora Store to its Root installer (`PREFERENCE_INSTALLER_ID=2`) with ownership preserved |
| Accessibility | Enables the JMGO key service + Projectivy accessibility service and notification listener by editing `settings_secure.xml` as root (`settings put` is blocked for these keys) |
| English settings | Deploys a fully translated Settings APK via boot-time bind mount (see [English settings](#english-settings)) |

Every step checks current state first. Re-running is safe.

## Compatibility

- Device: JMGO N1S 4K China (`K310`, MT9671, `armeabi-v7a`)
- Firmware: `1.1.31.x` (byte-verified by the root exploit; other versions abort safely)
- Connection: ADB over TCP (`<ip>:5555`). USB ports are host-only; there is no USB ADB and no `adb root` on this device.

## Prerequisites

1. Python 3.8+ with `PYTHONUTF8=1` (required on Windows for CJK-safe I/O).
2. Android platform-tools (`adb` on `PATH`).
3. Projector and computer on the same LAN with ADB reachable.
4. Working root via `/system/xbin/su` (full path — bare `su` resolves to the Magisk applet and denies without a policy row). If `adb shell /system/xbin/su id` does not return `uid=0`, complete the root step first.

## Quickstart

```powershell
$env:PYTHONUTF8="1"

# 1. Locate the projector (DHCP moves it)
python scripts/find_projector.py --subnet 192.168.1.0/24

# 2. Dry run — reports drift, changes nothing
python scripts/apply_tweaks.py --device 192.168.1.10:5555 --check

# 3. Apply
python scripts/apply_tweaks.py --device 192.168.1.10:5555

# 4. Apply including the English Settings APK (see below)
python scripts/apply_tweaks.py --device 192.168.1.10:5555 --en-apk ./en_setting.apk
```

Common options:

```powershell
# Skip steps (comma-separated)
python scripts/apply_tweaks.py --device <ip>:5555 --skip debloat,ensettings

# Custom timezone / device name
python scripts/apply_tweaks.py --device <ip>:5555 --timezone Asia/Singapore --device-name "Living Room"

# Silent su grant for an app UID (prompt UI never surfaces on this TV)
python scripts/apply_tweaks.py --device <ip>:5555 --grant-uid 10123 --skip locale,debloat,launcher,aurora,a11y,ensettings

# Install APKs before asserting HOME (TV Bro steals HOME on install, so HOME is fixed last)
python scripts/apply_tweaks.py --device <ip>:5555 --projectivy-apk ./projectivy.apk --tvbro-apk ./tvbro.apk
```

Reference verification run (see [`docs/STATE.md`](docs/STATE.md)):

```
== locale ==      current values reported; drift listed as would-run commands
== debloat ==     already disabled: com.jmgo.appstore, ... (10 packages)
== launcher ==    jmgo launcher frozen: True / Projectivy resumed
== magisk ==      zygisk: value=0 OK / policies: Aurora ALLOW only
== aurora ==      current installer id: 2 / already id=2
== a11y ==        a11y services OK: True (have 2, want 2) / already correct
== ensettings ==  bind active: True / ensettings already deployed
CHECK done — nothing changed.
```

## English settings

The stock Settings app forces `zh-rCN` internally, so patching the default
`values/` resources has no effect — `values-zh-rCN` must be patched.
The translated APK (~50 MB, re-signed) is intentionally not committed;
build it from the validated string map in this repo or attach it to a
GitHub Release.

- Source of truth: [`settings-i18n/overlay_en_strings.xml`](settings-i18n/overlay_en_strings.xml), [`settings-i18n/en_arrays.xml`](settings-i18n/en_arrays.xml)
- Pipeline: [`docs/SETTINGS_I18N.md`](docs/SETTINGS_I18N.md) (apktool + `zipalign -f -p 4`; full rebuilt APK required)
- Deploy: `--en-apk` pushes to `/data/local/tmp/en_setting.apk`, installs [`service.d/zz-en-settings.sh`](service.d/zz-en-settings.sh) to `/data/adb/service.d/`, then live bind-mounts over `/system/system_ext/app/JmGOSetting_OS8.0/JmGOSetting_OS8.0.apk` and force-stops `com.jmgo.setting.x`

Constraints (verified on-device, see [`docs/PROVEN_BROKEN.md`](docs/PROVEN_BROKEN.md)):

- The boot script must wait for `sys.boot_completed` (+15 s). Binding earlier makes PackageManager drop `com.jmgo.setting.x` (signature mismatch vs `packages.xml`). Live post-boot binds are always safe.
- The rebuild must be zipaligned last, otherwise `libGaussBlur.so` fails to load.

## Standalone helpers

| Script | Purpose |
| ------ | ------- |
| `scripts/find_projector.py` | Sweep a `/24` for port `5555` (64 threads) |
| `scripts/magisk_sql.py` | Query Magisk's DB, e.g. `--device <ip>:5555 "SELECT * FROM policies;"` |
| `scripts/secedit_apply.py` | Accessibility / notification-listener fix without the full pack (`--check`, `--reboot`) |
| `scripts/shot.py` | Binary-safe `screencap` via `exec-out` (`adb shell` corrupts `0A→0D0A`; JMGO prepends a wrapper line that is stripped) |

## Known limitations

- **DRM**: Widevine CDM does not instantiate on this firmware (`UnsupportedSchemeException`). Netflix / Disney+ / Prime require an external certified device. No fix is included here.
- **OTAs**: `com.jmgo.update` is protected. Decline system updates — an OTA can patch the root vector and wipe `/data`.
- **Zygisk must stay off** (`zygisk=0`): enabling it bootloops `system_server`. LSPosed is not viable on this box.
- **RRO overlays** for Settings are rejected (platform cert / `sharedUserId` mismatch); the bind-mount approach is the supported path.
- After an official reflash, `/system` is pristine: re-run the root exploit, then re-apply this pack. See [`docs/RECOVERY.md`](docs/RECOVERY.md).

## Project structure

```
README.md
docs/           STATE.md PROVEN_BROKEN.md RECOVERY.md FIRMWARE.md SETTINGS_I18N.md
scripts/        apply_tweaks.py find_projector.py magisk_sql.py secedit_apply.py shot.py
service.d/      zz-en-settings.sh zz-fix-su.sh
settings-i18n/  overlay_en_strings.xml en_arrays.xml
apk-source/     ExecCmd contract notes (root helper app)
```

Device backups (`boot.img`, `magisk_patched.img`, `jmgoenv_backup.img`),
toolchains, and built APKs are deliberately excluded via `.gitignore`.
Keep them offline; see [`docs/RECOVERY.md`](docs/RECOVERY.md).

## Troubleshooting

| Symptom | Action |
| ------- | ------ |
| `adb` connection refused | Re-sweep with `find_projector.py`; `adb disconnect` / `adb connect <new-ip>:5555` (adbd flaps offline after restarts) |
| `su id` is not `uid=0` | Use the full path `/system/xbin/su`; complete the root step first |
| HOME reverts after installing a browser | Re-run the pack — HOME is asserted last because some apps claim the HOME role on install; verify with `dumpsys activity … mResumedActivity` + `shot.py`, not `cmd shortcut` |
| Accessibility shows enabled but services stop | Reboot — `settings_secure.xml` edits take effect at boot; ownership must remain `system:system` mode `600` |
| Settings app missing after reboot | The EN APK was bound before PackageManager finished scanning — check `service.d` ordering (`boot_completed` + 15 s) and reinstall via `--en-apk` live |

## Contributing

Issues and PRs are welcome. Please include firmware version
(`getprop ro.build.version.incremental`), the full `--check` output, and a
screenshot (`scripts/shot.py`) where UI behavior is involved. Do not commit
device backups, keystores, APKs, or account tokens.

## License

MIT — see [LICENSE](LICENSE). Security research for hardware you own.
Use at your own risk; no warranty. This project is unaffiliated with JMGO.
