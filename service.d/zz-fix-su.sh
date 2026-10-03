#!/system/bin/sh
# Re-point /system/bin/su at the working jsu wrapper every boot.
# Something (Magisk boot setup) recreates /system/bin/su -> ./magisk,
# whose applet denies (empty policies, no prompt UI on TV).
mount -o rw,remount / 2>/dev/null
ln -sf /system/xbin/su /system/bin/su
mount -o ro,remount / 2>/dev/null
