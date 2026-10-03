# On-device state — 2026-10-02

Source: AGENTS.md §3 + live verification notes. Update this file after any
on-device change (date + what changed).

## Root / Magisk

- `/system/xbin/jsu` setuid `4750 root:shell` + `/system/xbin/su` wrapper
  (`-c` supported). Full path required.
- `/system` dm-verity ro; bind-mounts work; remount rw does not.
- `magiskd` running headless (patched boot flashed). Manager app
  UNINSTALLED. Zygisk OFF (`zygisk=0` in db).
- `/data/adb/magisk.db` `policies` = Aurora ALLOW only (uid 10051).
  Prompt UI never surfaces on this TV — grants only via direct DB insert:
  `INSERT OR REPLACE INTO policies VALUES(<uid>,2,0,1,0);`
- `service.d/`: `zz-en-settings.sh`, `zz-fix-su.sh`, `00-test.sh`.

## Settings i18n

- Bind active over
  `/system/system_ext/app/JmGOSetting_OS8.0/JmGOSetting_OS8.0.apk`.
- Deployed md5 `e81015b9…`, pristine md5 `c97345d7…`.
- App forces `zh-rCN`; EN build has zero Chinese left.

## Packages

Disabled (`pm disable-user`):

- appstore, ai.voice, arwen, gamecenter, bajintech.assistant, helpcenter,
  pinyin, miot, music, os.guide, jmgo.launcher (frozen for Projectivy)

Uninstalled: rootfix.doctor, LSPosed mgr, Magisk mgr, FlixVision,
morelocale.

Protected: `com.jmgo.update` (decline OTAs).

Installed: Projectivy 4.71 (default HOME
`com.spocky.projengmenu/.ui.home.MainActivity`, storage + installer
grants, a11y + notif listener; onboarding taps pending user), Aurora
(Root installer id=2, silent installs), TV Bro, ExecCmd (keep),
VLC/YouTube (stock).

## Settings

- tz `Asia/Hong_Kong`, locale en-US, name `JMGO N1S 4K`, Private DNS OFF.
- a11y: `com.jmgo.hippo/...JmgoKeyAccessibilityService:com.spocky.projengmenu/.services.ProjectivyAccessibilityService`,
  `accessibility_enabled=1`
- notif listener:
  `com.spocky.projengmenu/.services.notification.NotificationListener`
- Plex never installed — via Aurora by user.

## Open threads

1. User: Projectivy onboarding taps; Plex install via Aurora.
2. Optional: SmartTube if asked.
3. Leftover Chinese outside settings = other packages, per-screen rebuilds.
4. Keep declining OTAs.
