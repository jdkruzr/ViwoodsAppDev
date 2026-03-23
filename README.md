# Viwoods AiPaper Mini — E-Ink Fast Pen Input PoC

Android proof-of-concept for achieving fast, low-latency pen input on the **Viwoods AiPaper Mini** e-ink tablet from a third-party (non-system-signed) app.

The app uses Java reflection and Binder IPC to access Viwoods' e-ink APIs, enabling the T1000 timing controller to render pen strokes directly to the display — bypassing the normal Android rendering pipeline for near-instant ink feedback.

## How It Works

```
Pen input → T1000 hardware overlay (instant rendering)
                    ↓ (800ms after pen-up, overlay clears)
            App re-renders final strokes via Android Canvas
```

The key insight: the T1000 AutoDraw system can be activated from any app via Binder IPC. The system intercepts pen events at the native layer and renders strokes to the e-ink display before the app even receives touch events.

**Critical discovery:** `setAllRegionUnAutoDraw(false)` must be called — the device ships with all regions excluded from AutoDraw by default. Without this, AutoDraw is enabled but draws nowhere.

## Building

```bash
# Debug APK
./gradlew assembleDebug

# Release APK
./gradlew assembleRelease
```

**Requirements:** Android SDK 33, Java 11, Gradle 9.1.0

## Deploying to Device

ADB shell is disabled on this device. Deployment options:

- **Sideload** the APK via the file manager (copy to `/sdcard/Download/`)
- **ADB port forwarding** works (`adb forward`)
- **SSH** via Termux — see `tools/tablet_ssh.py`

## Architecture

The app consists of three files:

| File | Purpose |
|------|---------|
| `ENoteBridge.java` | Reflection-based bridge to the hidden `ENoteSetting` API. Tries wrapper methods first, falls back to direct binder calls, then to shell `service call` commands. |
| `MainActivity.java` | Programmatic UI with a pressure-sensitive `DrawView` that coordinates with the T1000 overlay timing (900ms delayed redraw after pen-up). |
| `NativeProbe.java` | Diagnostic tool that confirmed the direct JNI path (`libpaintworker.so`) is not viable from app process — requires system privileges. |

### Display Modes

| Mode | Value | Use |
|------|-------|-----|
| FAST | 4 | Pen input (fast partial refresh) |
| GL16 | 3 | Reading (default, 16-level gray) |
| GC | 17 | Full refresh (ghosting cleanup) |

## Device Info

- **Model:** Viwoods AiPaper Mini
- **OS:** Android 13 (SDK 33)
- **Display:** 1440×1920 e-ink (model SE05, SoftSolution type)
- **SoC:** MediaTek (kernel 4.19)
- **Timing chip:** T1000 (E Ink timing controller)

## Debugging

Logcat is inaccessible on this device (SELinux restrictions). The app writes diagnostics to `/sdcard/Download/`:

- `einkpoc_init.txt` — bridge initialization log
- `einkpoc_crash.txt` — uncaught exception stack traces
- `einkpoc_info.txt` — device/API status dump
- `einkpoc_nativeprobe.txt` — native library probe results

## Further Reading

See [`VIWOODS_APP_DEV.md`](VIWOODS_APP_DEV.md) for the full API reference, AIDL transaction codes, native method signatures, and exploration roadmap.
