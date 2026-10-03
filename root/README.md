# Root — `jmgo_root.py` (vendored, fixed)

One-click root for the JMGO N1S 4K, vendored from upstream
[Yurishizu9/jmgo-n1s-root](https://github.com/Yurishizu9/jmgo-n1s-root)
with two fixes (verified 2026-10-04):

1. **Embedded APK was truncated.** Upstream's `APK_B64` decodes to 5,178
   bytes and is not a valid zip (`BadZipFile`), while the real ExecCmd APK
   is 12,691 bytes — so `install_apk()` always failed upstream.
   This copy installs from `apk-build/execmd.apk` on disk instead.
2. **Binary-safe block reads.** Upstream's `read_raw()` uses `adb shell`
   with `bs=1`, which mangles binary (`0x0A` → `0x0D 0x0A`) and corrupts
   `struct` parsing. This copy uses `adb exec-out` with 4K blocks and
   slices the window (also far faster than byte-at-a-time).

## Use

```powershell
$env:PYTHONUTF8="1"
python root/jmgo_root.py <PROJECTOR_IP>
.\adb.exe -s <IP>:5555 shell "/system/xbin/su id"   # expect uid=0
```

Find the IP via the projector's File Manager → lan share (`local ip…`),
or `python scripts/find_projector.py --subnet 192.168.1.0/24`.

## Contents

- `jmgo_root.py` — fixed root script (patch offsets verified for
  firmware `1.1.31.x`; aborts safely on byte mismatch)
- `apk-build/execmd.apk` — working ExecCmd helper (uid 1000 via
  `SettingService.execCommand()`); 12 KB, committed via `.gitignore`
  exception
- `apk-source/` — ExecCmd source (`AndroidManifest.xml`, `MainActivity.java`)

After root succeeds, apply the tweak pack:
`python scripts/apply_tweaks.py --device <IP>:5555 --check` first.
