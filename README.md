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

## Maintainer workflows

**Bump version** and **Build** are independent manual Actions workflows. Select the
source branch/ref with GitHub's built-in selector. Bump has only the patch/minor/major
choice and requires a branch; **Build has zero custom inputs** and accepts any
selected ref. Every checkout uses the immutable dispatch `github.sha`. Neither
workflow runs on push or pull request. Publishing a migration branch/PR does not
compile or sign anything.

The source authority is the coordinated `MARKETING_VERSION` and
`CURRENT_PROJECT_VERSION` contract in the latest original Bump header
(`d50cef9572123ee31fdf1e43e05ff2afd9332db3`), which superseded the earlier
marketing-only header (`4ccb3dbf5d8968be572eea36b54fbc3a1af2ee4c`). Its implementation
accidentally validated/wrote only the marketing-first key. At migration intake,
marketing and source `Info.plist` agree on **2.1.5**; that version is not incremented.
Only stale source current settings (2.1.1) and the two display-version fields in
source `English.lproj/InfoPlist.strings` (2.1.0) are repaired to 2.1.5.

Future bumps require canonical `X.Y.Z` and consistency across all six settings
for each key, source plist and source localization. Literals are co-bumped;
supported Xcode references are preserved and resolved, never flattened.
Optional `CFBundleVersion` stays absent when absent. Duplicate/missing/invalid
fields fail before writing. Rewrites preserve BOM, each individual CR/LF/CRLF,
permissions and unrelated bytes. Prebuilt bundles/localizations, dependencies,
Windows payload, 4D data/schema counters and manifest command IDs are not source
version inputs or edits.

Bump requires a clean checkout and exact selected remote branch SHA. It produces
one nonempty source-only commit with one direct parent and the Copilot co-author
trailer. The executable pre-push guard is mandatory both initially and immediately
before pushing: it checks Git's advertised old SHA/ref, literal new SHA/HEAD and
exactly one update, rejecting advance/rewind/delete/same-result races. The explicit
nonforce branch push disables followed tags with both `push.followTags=false` and
`--no-follow-tags`. Bump creates no tag/release and dispatches no build. If the branch
moves, inspect the retained local commit and dispatch afresh from the new branch
head; do not force-push or amend.

Build derives `vX.Y.Z` and `Custom Window-X.Y.Z.zip`/`.dmg` from selected source.
A constant cross-branch publication concurrency group queues builds without
cancelling. Authenticated, fully paginated release lists (including drafts) and
an exact remote-tag absence check run before native work and again **after**
build, sign, strict verification, both successful `Accepted` notary submissions
and stapling. API/auth/network/404/malformed responses fail closed.

The original pipeline is macOS-only despite its old Windows comments. It retains
the `Default` target configuration, `arm64 x86_64`, original **10.13** workflow
deployment override, Cocoa/resource phases, signing commands and secret names.
It explicitly resolves the potential `Default` sibling output to `test/Plugins`,
invalidating only generated binary/plist/localization/signature and intermediates.
It never removes the whole bundle, resource tree, Windows payload or dependencies.
Required architecture tokens are exact; extra slices are not forbidden.
Built plist/localization metadata is checked (XML/binary plist, normal strings
or UTF-16 BOM strings), including optional-key absence. The real resource
destinations `Contents/Resources/manifest.json` and `constants.xlf` must match
their sources.

### Publication recovery

Publication is create-only: separate `POST git/refs` at the selected SHA, exact
remote verification, `POST` of a **new public, non-prerelease** release with explicit
tag/name/target/body/flags, then separate uploads to its returned release ID.
The original workflow had no release body or generated notes; the body remains
empty. No reuse, update, PATCH, delete, clobber, rollback or automatic retry occurs.

On any failure, **all partial remote state is retained**. Read the failed step's
error and recorded tag/release ID; inspect the exact tag SHA, draft/public release
and uploaded assets before deciding what to do. A tag-only failure, release-create
failure or first/second upload failure blocks rerunning the same version. Never
blindly rerun, delete/retarget tags, overwrite assets or amend the source commit.
Recovery requires a maintainer decision: preserve the evidence and intentionally
complete retained state outside this create-only workflow, or use a newly bumped
version. The workflow never cleans up published state for you.

### Offline validation

Run `actionlint` and `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -v`.
The full suite is source-derived and also runs after a genuine guarded helper
bump in a disposable Git/bare-origin fixture: after committing the migration, run
`PYTHONDONTWRITEBYTECODE=1 python3 .github/tests/validate_bumped.py`.
Tests cover real Git races,
pagination/API errors, create payloads, retained partial state, byte preservation,
inline duplicates, and extracted workflow shell blocks with a closed PATH of
native stubs. There are no PowerShell blocks in this macOS-only pipeline.
These checks do **not** constitute native compilation, signing or notarization proof.

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
