# English settings rebuild

Source of truth: `settings-i18n/overlay_en_strings.xml` (validated EN map)
+ `settings-i18n/en_arrays.xml`.

## One-time setup

1. Pull device framework: `adb pull /system/framework/framework-res.apk`
2. `apktool if framework-res.apk`
3. Decode pristine: `apktool d jmgo_setting.apk -o setting_dec`
   (never leave `*.origbak` inside `setting_dec/res/`)

## Rebuild

1. Patch `setting_dec/res/values-zh-rCN/strings.xml` **by NAME** from the
   validated EN map. Placeholders (`%1$s`, `%d`) and escapes must survive.
   Patch that file only; ignore `zh-rHK`/`zh-rTW`. Default `values/` alone
   is NOT enough — the app renders `zh-rCN`.
2. `apktool b setting_dec -o en_setting_unaligned.apk`
3. `zipalign -f -p 4 en_setting_unaligned.apk en_setting.apk` — REQUIRED.
   Unaligned builds crash with `UnsatisfiedLinkError libGaussBlur.so`.
4. Do NOT transplant just `resources.arsc` into the original zip
   (`abc_vector_test.xml` missing due to obfuscated `res/-0.xml` names).
   Use the FULL rebuilt APK.

## Deploy

Live (safe anytime post-boot):

```powershell
adb push en_setting.apk /data/local/tmp/en_setting.apk
adb shell "/system/xbin/su mount -o bind /data/local/tmp/en_setting.apk /system/system_ext/app/JmGOSetting_OS8.0/JmGOSetting_OS8.0.apk"
adb shell "am force-stop com.jmgo.setting.x"
```

Persistent: `service.d/zz-en-settings.sh` (waits `sys.boot_completed`
+15 s — binding earlier makes PMS drop the package).
