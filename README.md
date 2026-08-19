![version](https://img.shields.io/badge/version-16%2B-8331AE)
![platform](https://img.shields.io/static/v1?label=platform&message=mac-intel%20|%20mac-arm&color=blue)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-custom-window)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-custom-window/total)

# 4d-plugin-custom-window

Custom Window lets you make a 4D form window transparent and fade its opacity in and out, by driving Cocoa's `NSWindow` directly on macOS. There is no Windows implementation — every command resolves the window through `NSWindow`/`AppKit` and only compiles under `VERSIONMAC`.

| Command | Returns | Purpose |
|---|---|---|
| [`SET WINDOW TRANSPARENT`](#set-window-transparent) | — | Makes a window's background fully transparent. |
| [`SET WINDOW ALPHA`](#set-window-alpha) | — | Animates a window's overall opacity to a target value. |
| [`Get window alpha`](#get-window-alpha) | Real | Reads a window's current opacity. |

**Platforms:** macOS (Intel and Apple Silicon) only. No Windows support.

---

## Requirements & platform notes

- **4D 16 or later.** On 4D **v17 and earlier**, `manifest.json` must be moved into the plugin's `Contents` folder for 4D to pick it up — on v18+ it stays at the plugin's top level.
- **macOS only.** All three commands go through `NSWindow`; there is no Windows code path at all, so none of these commands do anything on Windows builds.
- **A transparent window loses its normal drag handle.** After calling `SET WINDOW TRANSPARENT`, place an invisible button using `DRAG WINDOW` on the form so the user can still move the window — this isn't optional, since the window's own chrome is no longer usable for dragging once its background is cleared.
- **`SET WINDOW ALPHA` is not thread-safe.** Call it from the main process/main thread of your 4D method. (The plugin internally marshals every command onto the main thread before touching `NSWindow`, but the underlying Cocoa animation API this command drives is documented by the plugin's author as not thread-safe, so don't rely on calling it concurrently from preemptive processes.)
- **Invalid or closed window references fail silently, not with a 4D error.** All three commands guard on the window pointer resolving successfully; if it doesn't (e.g. a stale or already-closed window reference), `SET WINDOW TRANSPARENT`/`SET WINDOW ALPHA` simply do nothing, and `Get window alpha` returns `0`. There's no error/exception raised in any case — check for a window you know is still open rather than relying on this to fail loudly.

---

## SET WINDOW TRANSPARENT

### Syntax

```4d
SET WINDOW TRANSPARENT ( window )
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | Window reference, as returned by a command like `Open form window`. |
| Result | — | No return value. |

### Description

Clears the window's background color and sets it non-opaque, so anything not explicitly drawn by your form shows through to whatever is behind the window on screen. This is a one-way visual change — there's no "un-transparent" command in this plugin; if you need to restore an opaque window, close and reopen it.

If `window` doesn't resolve to a live window (already closed, or an invalid reference), the command does nothing — no error is raised.

Because a transparent window's default chrome (title bar, edges) is no longer a usable drag target, place an invisible button with the `DRAG WINDOW` action on the form so users can still reposition it.

### Example

From the plugin's own README:
```4d
$window:=Open form window("Form1";Modal form dialog box)
SET WINDOW TRANSPARENT ($window)
DIALOG("Form1")
```

Same pattern with a non-modal window and an explicit close:
```4d
var $window : Integer
$window:=Open form window("Overlay";Movable form dialog box)
SET WINDOW TRANSPARENT ($window)
DIALOG("Overlay")
CLOSE WINDOW($window)
```

---

## SET WINDOW ALPHA

### Syntax

```4d
SET WINDOW ALPHA ( window ; alpha ; duration )
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | Window reference, as returned by a command like `Open form window`. |
| `alpha` | Real | Target opacity, from `0` (fully transparent) to `1` (fully opaque). Values outside this range are clamped: anything ≤ 0 becomes `0`, anything > 1 becomes `1`. |
| `duration` | Real | Animation duration in seconds, from `0` to `9`. Values outside this range are clamped the same way: negative becomes `0`, anything > 9 becomes `9`. Use `0` for an instant change with no animation. |
| Result | — | No return value. |

### Description

Animates the window's overall opacity (not just its background — the whole window, including its contents) from its current value to `alpha` over `duration` seconds, using Cocoa's animator proxy. All three parameters are read unconditionally, so there's no optional form — always pass all three.

If `window` doesn't resolve to a live window, the command does nothing — no error is raised, and no animation occurs.

**Not thread-safe** — call this from your method's own main-thread execution, not from a preemptive process running concurrently against the same window.

### Example

Fade a window fully in over half a second:
```4d
$window:=Open form window("Panel";Movable form dialog box)
SET WINDOW ALPHA ($window;1;0.5)
DIALOG("Panel")
```

Fade out before closing, using the clamp behavior to just pass an out-of-range duration instead of computing it:
```4d
SET WINDOW ALPHA ($window;0;9)  // clamps to the 9-second max anyway
CLOSE WINDOW($window)
```

Instant, unanimated change (`duration` of `0`):
```4d
SET WINDOW ALPHA ($window;0.5;0)
```

---

## Get window alpha

### Syntax

```4d
alpha:=Get window alpha ( window )
```

| Parameter | Type | Description |
|---|---|---|
| `window` | Longint | Window reference, as returned by a command like `Open form window`. |
| Result | Real | Current opacity of `window`, from `0` to `1`. |

### Description

Reads back the window's current alpha value directly from `NSWindow`, so it reflects the live value even mid-animation from a previous `SET WINDOW ALPHA` call, not just the last value you set.

If `window` doesn't resolve to a live window, this returns `0` rather than raising an error — so a `0` result is ambiguous between "genuinely fully transparent" and "invalid window reference." If that distinction matters to your code, track window validity yourself (e.g. keep the reference only while you know the window is open) rather than inferring it from this return value.

### Example

```4d
$window:=Open form window("Panel";Movable form dialog box)
SET WINDOW ALPHA ($window;0.4;1)
 // ... later, e.g. from a form method while the fade may still be in progress
$current:=Get window alpha ($window)
If ($current<0.5)
   // still mostly faded out
End if
```

---

## Error handling & troubleshooting

- **No visible effect at all:** the most common cause is an invalid or stale `window` reference — all three commands silently no-op (or return `0` for `Get window alpha`) rather than raising a 4D error. Confirm the window reference came from a still-open window.
- **Window won't move after `SET WINDOW TRANSPARENT`:** expected — the transparent window's normal chrome is no longer draggable. Add an invisible button with `DRAG WINDOW` to the form.
- **`Get window alpha` returns `0` and you expected a real value:** this is indistinguishable from an invalid window reference in the command's own return value; verify separately that the window is still open.
- **Animating `SET WINDOW ALPHA` from a preemptive process/thread:** don't — the command is documented as not thread-safe. Drive it from your method's normal (non-preemptive) execution.
- **Building against 4D v17 or earlier:** move `manifest.json` into the plugin's `Contents` folder, or 4D won't pick up the command declarations.
- **Windows builds:** there is nothing to troubleshoot — these commands have no Windows implementation and won't compile/link on that platform.

---

## Quick reference

```4d
 // Transparent, draggable-via-button window
$window:=Open form window("Form1";Modal form dialog box)
SET WINDOW TRANSPARENT ($window)
DIALOG("Form1")

 // Fade a window in, check progress, fade it out, close it
$window:=Open form window("Panel";Movable form dialog box)
SET WINDOW ALPHA ($window;1;0.5)
$current:=Get window alpha ($window)
SET WINDOW ALPHA ($window;0;0.5)
CLOSE WINDOW($window)
```
