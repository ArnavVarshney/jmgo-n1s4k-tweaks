#!/system/bin/sh
# English settings via bind-mount.
# MUST run AFTER PackageManager finishes its boot scan: PMS rejects the
# re-signed APK (sig mismatch vs packages.xml), so binding before/during
# the scan unregisters com.jmgo.setting.x entirely. Waiting for
# sys.boot_completed guarantees PMS is done; runtime APK reads are never
# signature-checked, so post-boot bind + force-stop is safe.
# (Magisk service.d runs this in background; the wait loop is fine.)
for i in $(seq 1 150); do
  if [ "$(getprop sys.boot_completed)" = "1" ]; then break; fi
  sleep 2
done
sleep 15
ORIG=/system/system_ext/app/JmGOSetting_OS8.0/JmGOSetting_OS8.0.apk
PATCHED=/data/local/tmp/en_setting.apk
if [ -f "$PATCHED" ]; then
  mount -o bind "$PATCHED" "$ORIG"
  log -t EnSettings "bind rc=$?"
  # settings may have started with the Chinese APK; restart it into English
  am force-stop com.jmgo.setting.x 2>/dev/null
else
  log -t EnSettings "patched apk missing, skipping"
fi
