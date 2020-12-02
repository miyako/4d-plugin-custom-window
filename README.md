# 4d-plugin-custom-window
Set window transparent on Mac

### Platform

| carbon | cocoa | win32 | win64 |
|:------:|:-----:|:---------:|:---------:|
| |<img src="https://cloud.githubusercontent.com/assets/1725068/22371562/1b091f0a-e4db-11e6-8458-8653954a7cce.png" width="24" height="24" /> | | 

### Version

<img width="32" height="32" src="https://user-images.githubusercontent.com/1725068/73986501-15964580-4981-11ea-9ac1-73c5cee50aae.png"> <img src="https://user-images.githubusercontent.com/1725068/73987971-db2ea780-4984-11ea-8ada-e25fb9c3cf4e.png" width="32" height="32" />

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
