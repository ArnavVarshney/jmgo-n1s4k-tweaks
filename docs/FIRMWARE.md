# Firmware

No verified K310 China link exists (as of 2026-10-02).

- MUST be N1S 4K China (**K310**). Other models = brick risk. Local zips
  are signature-verified (tampered fails safe), but wrong-model official
  zips are still dangerous.
- Channels: `www.jmgo.com` online support / `service@jmgo.com` for
  `update_jmgo.zip`; `yuque.com/jmgo/dl`; on-device online upgrade (may
  patch the vuln — check version after); touying/znds forums (last resort).
- Flash: FAT32 USB, `update_jmgo.zip` at root, Settings → local upgrade,
  keep power on. May wipe `/data`.
- `com.jmgo.update` is protected — keep declining OTAs until you have a
  verified re-root path for the new firmware.
