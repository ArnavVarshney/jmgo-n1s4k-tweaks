# Proven broken — do not retry without new information

- **Zygisk ON** → `system_server` SIGABRT bootloop (`NewDirectByteBuffer`
  absurd capacity). Keep `zygisk=0`. LSPosed dead here.
- **Frida 17.x** segfaults every injected process. Java bridge unusable
  (`invalid instruction`). `dev.spawn` stalls on `usap32`. Only
  Frida 16.7.19 + pure-native Interceptor hooks work; nothing needs them now.
- **RRO overlay** for settings: rejected (cert mismatch, no overlayable,
  `sharedUserId=android.uid.system`).
- **Bind-mounting the APK before PMS boot scan** unregisters
  `com.jmgo.setting.x` (sig mismatch vs `packages.xml`). Service script MUST
  wait for `sys.boot_completed` (+15 s), then bind + `am force-stop`.
  Live post-boot binds are always safe.
- **Patching only default `values/`** insufficient — app renders
  `values-zh-rCN`. Patch that file only.
- **Transplanting just `resources.arsc`** crashes (`abc_vector_test.xml`
  missing; obfuscated `res/-0.xml` names). Use FULL rebuilt APK.
- **Unaligned rebuild** → `UnsatisfiedLinkError libGaussBlur.so`. Always
  `zipalign -f -p 4` last.
- **apktool link** fails vs stock framework (private `android:color/...`)
  and on stray files: pull device `framework-res.apk` → `apktool if`,
  never leave `.origbak` inside `setting_dec/res/`.
- `settings put` for `enabled_accessibility_services` BLOCKED — edit
  `/data/system/users/0/settings_secure.xml` as root, preserve
  `system:system` 600, reboot.
- `cmd shortcut get-default-launcher` LIES; trust
  `dumpsys activity ... mResumedActivity` + screenshots.
- TV Bro steals HOME role on install — re-assert Projectivy after.
- `pm grant WRITE_SECURE_SETTINGS` fails if app doesn't declare it.
- Widevine CDM unfixable (`UnsupportedSchemeException`). Use certified stick.
  FlixVision (`com.netflix.sv1`) was pirate — removed.
