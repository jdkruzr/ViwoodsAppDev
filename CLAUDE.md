# CLAUDE.md — Viwoods AiPaper Mini E-Ink PoC

## Project Overview

Android proof-of-concept app for fast pen input on the **Viwoods AiPaper Mini** e-ink tablet. Uses reflection and binder IPC to access Viwoods' proprietary e-ink fast-rendering APIs from a third-party (non-system-signed) app.

**Package:** `com.example.einkpoc`
**Target device:** Viwoods AiPaper Mini (Android 13, SDK 33, 1440×1920 e-ink display)

## Repository Structure

```
ViwoodsAppDev/
├── app/
│   ├── build.gradle                          # Module build config (compileSdk 33, Java 11)
│   └── src/main/
│       ├── AndroidManifest.xml               # Permissions (storage access)
│       └── java/com/example/einkpoc/
│           ├── MainActivity.java             # UI + DrawView (pressure-sensitive canvas)
│           ├── ENoteBridge.java              # Reflection bridge to ENoteSetting APIs
│           └── NativeProbe.java              # Diagnostic probe for libpaintworker.so
├── tools/
│   └── tablet_ssh.py                         # SSH helper for device communication
├── build.gradle                              # Root build (AGP 8.7.0)
├── settings.gradle                           # Gradle project settings
├── gradle.properties                         # JVM config, AndroidX enabled
├── VIWOODS_APP_DEV.md                        # Detailed API reference & exploration notes
└── CLAUDE.md                                 # This file
```

## Tech Stack

- **Language:** Java (source/target compatibility: Java 11)
- **Platform:** Android 13 (SDK 33) — both minSdk and targetSdk are 33
- **Build system:** Gradle 9.1.0, Android Gradle Plugin 8.7.0
- **Dependencies:** None beyond the Android framework (pure framework implementation)
- **No testing framework** configured (no JUnit, Espresso, etc.)
- **No linter/formatter** configured
- **No CI/CD** pipelines

## Build & Deploy

```bash
# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Clean
./gradlew clean
```

**Deployment to device:** ADB shell is disabled on this device. Use `adb install` alternatives or sideload via file manager. Port forwarding (`adb forward`) works. SSH access via Termux is available (see `tools/tablet_ssh.py`).

## Architecture & Key Concepts

### Three Source Files

1. **`ENoteBridge.java`** — The core abstraction. Wraps Viwoods' hidden `android.os.enote.ENoteSetting` API using Java reflection. Falls back through three invocation strategies:
   - Wrapper methods via `ENoteSetting.getInstance()` (reflection)
   - Direct binder service calls via extracted `IENoteSetting` interface (reflection)
   - Shell `service call ENoteSetting <txn_code>` via `Runtime.exec()` (fallback)

2. **`MainActivity.java`** — UI built programmatically (no XML layouts). Contains `DrawView`, a custom View with pressure-sensitive stroke rendering that coordinates with the T1000 AutoDraw overlay (delays app redraw by 900ms after pen-up to avoid visual conflict with the 800ms overlay clear).

3. **`NativeProbe.java`** — Diagnostic tool that probes `libpaintworker.so` method-by-method. Each step is independently error-handled. **Conclusion: direct JNI path is NOT viable from app process** (requires system privileges).

### Fast Ink Path (Working Approach)

The app uses **AutoDraw via Binder IPC** — the T1000 timing controller renders strokes directly to the e-ink display before the app receives touch events:

```
App → ENoteBridge (reflection/binder) → system_server → T1000 hardware overlay
```

Setup sequence: `setPictureMode(4)` → `setT1000AutoDrawEnable(true)` → `setAllRegionUnAutoDraw(false)` → `setAutoDrawToolType(2)` → `setAutoDrawPenWidthRange(min, max)` → `addAutoDrawRect(0, 0, w, h)`

### Display Modes

| Mode | Value | Use |
|------|-------|-----|
| MODE_FAST | 4 | Pen input (fast partial refresh) |
| MODE_GL16 | 3 | Reading (default, 16-level gray) |
| MODE_GC | 17 | Full refresh (ghosting cleanup) |

## Code Conventions

- **No XML layouts** — all UI is built programmatically in Java
- **Reflection-heavy** — all ENoteSetting access uses `Class.forName` / `getMethod` / `invoke`
- **File-based logging** — logcat is inaccessible on device; diagnostics write to `/sdcard/Download/einkpoc_*.txt`
- **Crash handler** — global `UncaughtExceptionHandler` writes stack traces to `/sdcard/Download/einkpoc_crash.txt`
- **Error return convention** — ENoteBridge methods return `String` results: `"OK"`, `"OK (binder)"`, `"OK (shell:0)"`, or `"FAIL:<reason>"`
- **TAG constants** — each class defines `private static final String TAG` for logging
- **Minimal dependencies** — no third-party libraries; pure Android framework
- **No ProGuard/R8** — `minifyEnabled false` in release builds

## Important Caveats

- **ADB shell is disabled** on this device — custom ADB daemon rejects shell commands
- **logcat is not accessible** from Termux (SELinux restrictions)
- **`libpaintworker.so` JNI path is dead** — requires `/dev/t1000_spi`, `SurfaceComposerClient`, libusb (all system-only)
- **AutoDraw overlay is ephemeral** — strokes vanish after 800ms; app must re-render final content
- **`setAllRegionUnAutoDraw(false)`** is the critical discovery — without it, AutoDraw is enabled but draws nowhere

## Reference Documentation

See **`VIWOODS_APP_DEV.md`** for the full API reference including:
- All AIDL transaction codes for `service call` usage
- ENoteSetting wrapper method signatures
- ENoteWriting native JNI method signatures
- Device hardware specs and system properties
- FocusMonitorService third-party app overlay details
- Exploration roadmap and open questions

## Device Access

- **SSH:** Via Termux — `tools/tablet_ssh.py` (IP: 192.168.8.156, port 8022)
- **ADB forward:** Works for port forwarding
- **File transfer:** Via `/sdcard/Download/` (app writes debug logs here)
