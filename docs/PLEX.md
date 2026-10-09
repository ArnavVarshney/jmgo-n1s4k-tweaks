# Plex (patched build)

Plex 2026.19.1 from Aurora crashed ~4s after every launch:

```
java.lang.RuntimeException: Call setApplication from Application onCreate before using this API
    at tv.vizbee.screen.api.Vizbee.initialize(...)
    at tv.vizbee.rnreceiver.RNVizbeeNativeManager.init(...)
FATAL EXCEPTION: mqt_v_native -> process dies, MainActivity force-finished
```

Plex's React Native layer initializes the Vizbee Cast SDK without the
required `setApplication()` call. Deterministic app bug, not an install
problem (correct `armeabi-v7a` splits were installed).

## Fix applied (2026-10-09)

Single-method no-op: `Vizbee.initialize(String, VizbeeAppAdapter,
VizbeeOptions)` returns immediately. Manifest untouched; all four APKs
(base + splits) re-signed with one local key and installed via
`adb install-multiple`. Verified: no FATAL, process alive 35s+,
`tv.plex.app.MainActivity` resumed. Plex blacklisted in Aurora
(`ignored_update`) so it is never "updated" back to the broken
Play-signed build.

- Vizbee Cast-receive is dead by design (it needs Play Services Cast,
  absent here; mocking `setApplication` would only move the crash).
  Plex-to-Plex Companion fling uses Plex's own LAN protocol and is unaffected.
- Billing init (needs Play Store) already fails gracefully — untouched.
- On each Plex update the patch must be re-applied with the SAME key
  (full recipe in workspace `plexfix/NOTES.md`); otherwise uninstall first.
- Unrelated, still true: Widevine CDM is broken on this box, so DRM'd
  Plex free content won't play; personal-media direct play is fine.
