# Recovery

## After an official reflash

`/system` is pristine (jsu WITH setuid, additions gone, Magisk gone from
boot). `/data` may be wiped.

1. Verify jsu setuid present:
   `adb shell ls -l /system/xbin/jsu`
2. `$env:PYTHONUTF8="1"; python jmgo_root.py <ip>`
3. If byte-verify fails — firmware patched the vuln. STOP, do not force.
4. Re-apply this repo: `python scripts/apply_tweaks.py --device <ip>:5555 --en-apk <path>`
5. Re-check HOME/roles with screenshot (`scripts/shot.py`).

## After DHCP move

ADB target moves. Sweep the subnet:

```powershell
python scripts/find_projector.py --subnet 192.168.51.0/24
```

then `adb disconnect` / `adb connect <new-ip>:5555` (adbd flaps offline
after restarts).

## Safe reboot

Long-press power = safe reboot. `adb reboot recovery` = dead TCP adb
(USB host-only ports). Recovery has no network adb.

## Backups to keep offline (not in git)

- `boot.img`, `magisk_patched.img`, `jmgoenv_backup.img`, `factory_a.img`
- pristine `jmgo_setting.apk` (md5 `c97345d7…`)
- `framework-res.apk` (for apktool)
