# 4d-plugin-custom-window
Set window transparent on Mac 64-bit (15R3 or later)

###Platform

| carbon | cocoa | win32 | win64 |
|:------:|:-----:|:---------:|:---------:|
| |<img src="https://cloud.githubusercontent.com/assets/1725068/22371562/1b091f0a-e4db-11e6-8458-8653954a7cce.png" width="24" height="24" /> | | 

###Version



<img src="https://cloud.githubusercontent.com/assets/1725068/22371270/93e3661c-e4d9-11e6-9021-4a9754c70630.png" width="32" height="32" /> <img src="https://cloud.githubusercontent.com/assets/1725068/18940648/2192ddba-8645-11e6-864d-6d5692d55717.png" width="32" height="32" />

###Syntax

```
SET WINDOW TRANSPARENT (window)
```

Parameter|Type|Description
------------|------|----
window|INT32|The window reference

**Note**: You need to place an invisible button with ``DRAG WINDOW`` to move the window around.

###Example

```
If (Form event=On Load)
	SET WINDOW TRANSPARENT (Current form window)
End if 
```

![](image.png)
