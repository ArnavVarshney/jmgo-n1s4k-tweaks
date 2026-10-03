# apk-source — ExecCmd helper app

Tiny app that exposes JMGO's unprotected `SettingService.execCommand()` so
`jmgo_root.py` can run commands as system user (uid 1000).

The full Android-Studio source lives in the original root workspace
(`apk-source/`, key `debug.keystore`). It is intentionally NOT duplicated
here — this folder just records the contract `apply_tweaks.py` relies on:

```
am start -n com.exec.cmd/.MainActivity -e cmd '<single command>'
```

- Runs as uid 1000; args are space-split, NO shell features.
- Keep the app installed (harmless, useful for forensics).
- Complex/quote-heavy commands FAIL through the wrapper — push a script
  file and run it instead of fighting quoting layers.
