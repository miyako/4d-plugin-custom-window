![platform](https://img.shields.io/static/v1?label=platform&message=osx-64&color=blue)
![version](https://img.shields.io/badge/version-16%2B-8331AE)
[![license](https://img.shields.io/github/license/miyako/4d-plugin-custom-window)](LICENSE)
![downloads](https://img.shields.io/github/downloads/miyako/4d-plugin-custom-window/total)

# 4d-plugin-custom-window
Set window transparent on Mac

To use on v16 or v17, move manifest.json to contents.

### Syntax

```
SET WINDOW TRANSPARENT (window)
```

Parameter|Type|Description
------------|------|----
window|LONGINT|The window reference

**Note**: You need to place an invisible button with ``DRAG WINDOW`` to move the window around.

### Examples

```
$window:=Open form window("Form1";Modal form dialog box)
SET WINDOW TRANSPARENT ($window)
DIALOG("Form1")
```

![](image.png)

```
SET WINDOW ALPHA (window;alpha;duration)
```

Parameter|Type|Description
------------|------|----
window|LONGINT|The window reference
alpha|REAL|
duration|REAL|

``SET WINDOW ALPHA`` is not thread safe

```
alpha:=Get window alpha (window)
```

Parameter|Type|Description
------------|------|----
window|LONGINT|The window reference
alpha|REAL|
